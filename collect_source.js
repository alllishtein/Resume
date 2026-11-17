#!/usr/bin/env node

/**
 * collect_source.js
 * جمع‌آوری همه فایل‌های سورس یک سرویس و ذخیره فشرده برای ارسال به Claude
 *
 * استفاده:
 *   node collect_source.js <path-to-service-folder> [options]
 *
 * گزینه‌ها:
 *   --out <file>       مسیر خروجی (پیش‌فرض: کنار پوشه ورودی با نام سرویس)
 *   --no-compress      خروجی plain text بدون gzip
 *   --ext <exts>       پسوندهای اضافه جدا با کاما (پیش‌فرض: cs,csproj,json,yaml,yml,xml,md,txt,env,config,toml,sh,ps1,dockerfile,proto)
 *   --ignore <dirs>    پوشه‌های نادیده‌گیری شده جدا با کاما (پیش‌فرض: bin,obj,node_modules,.git,dist,publish,.vs)
 *   --max-file-kb <n>  حداکثر سایز هر فایل به کیلوبایت (پیش‌فرض: 500)
 *   --help             نمایش راهنما
 *
 * مثال:
 *   node collect_source.js D:\Dezhban\dejban_backend_new\ACLServer
 *   node collect_source.js D:\Dezhban\dejban_backend_new\DCC --out C:\temp\dcc.txt.gz
 *   node collect_source.js D:\Dezhban\dejban_backend_new\Common --no-compress
 */

const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

// ─── پارس آرگومان‌ها ───────────────────────────────────────────────────────────

function parseArgs() {
    const args = process.argv.slice(2);
    if (args.length === 0 || args.includes('--help')) {
        printHelp();
        process.exit(0);
    }

    const opts = {
        inputPath: null,
        outFile: null,
        compress: true,
        extensions: new Set([
            'cs', 'csproj', 'sln',
            'json', 'yaml', 'yml', 'xml',
            'md', 'txt', 'env', 'config', 'toml',
            'sh', 'ps1', 'bat', 'cmd',
            'dockerfile', 'proto', 'graphql',
            'html', 'css', 'js', 'ts', 'jsx', 'tsx',
            'sql', 'http', 'rest'
        ]),
        ignoreDirs: new Set([
            'bin', 'obj', 'node_modules', '.git', 'dist',
            'publish', '.vs', '.idea', 'TestResults', 'coverage',
            '__pycache__', '.next', 'out'
        ]),
        maxFileSizeKb: 500,
    };

    for (let i = 0; i < args.length; i++) {
        const arg = args[i];
        if (arg === '--no-compress') {
            opts.compress = false;
        } else if (arg === '--out' && args[i + 1]) {
            opts.outFile = args[++i];
        } else if (arg === '--ext' && args[i + 1]) {
            args[++i].split(',').forEach(e => opts.extensions.add(e.trim().toLowerCase().replace(/^\./, '')));
        } else if (arg === '--ignore' && args[i + 1]) {
            args[++i].split(',').forEach(d => opts.ignoreDirs.add(d.trim().toLowerCase()));
        } else if (arg === '--max-file-kb' && args[i + 1]) {
            opts.maxFileSizeKb = parseInt(args[++i], 10);
        } else if (!arg.startsWith('--')) {
            opts.inputPath = arg;
        }
    }

    if (!opts.inputPath) {
        console.error('❌ خطا: پوشه ورودی را مشخص کنید.');
        printHelp();
        process.exit(1);
    }

    return opts;
}

function printHelp() {
    console.log(`
collect_source.js — جمع‌آوری سورس کد برای ارسال به Claude

استفاده:
  node collect_source.js <path> [--out <file>] [--no-compress] [--ext <exts>] [--ignore <dirs>] [--max-file-kb <n>]

مثال‌ها:
  node collect_source.js D:\\Dezhban\\ACLServer
  node collect_source.js D:\\Dezhban\\DCC --out C:\\temp\\dcc.txt.gz
  node collect_source.js D:\\Dezhban\\Common --no-compress
  node collect_source.js D:\\Dezhban\\RequestTracker --max-file-kb 200
`);
}

// ─── پیمایش پوشه‌ها ────────────────────────────────────────────────────────────

function walkDir(dirPath, opts, collected = []) {
    let entries;
    try {
        entries = fs.readdirSync(dirPath, { withFileTypes: true });
    } catch {
        return collected;
    }

    for (const entry of entries) {
        const fullPath = path.join(dirPath, entry.name);

        if (entry.isDirectory()) {
            const nameLower = entry.name.toLowerCase();
            if (!opts.ignoreDirs.has(nameLower)) {
                walkDir(fullPath, opts, collected);
            }
            continue;
        }

        if (!entry.isFile()) continue;

        const ext = path.extname(entry.name).toLowerCase().replace(/^\./, '');
        const baseLower = entry.name.toLowerCase();

        // فایل بدون پسوند به اسم dockerfile یا .env
        const isSpecialFile =
            baseLower === 'dockerfile' ||
            baseLower === '.env' ||
            baseLower === '.gitignore' ||
            baseLower === 'makefile';

        if (!opts.extensions.has(ext) && !isSpecialFile) continue;

        let stat;
        try {
            stat = fs.statSync(fullPath);
        } catch {
            continue;
        }

        const sizeKb = stat.size / 1024;
        if (sizeKb > opts.maxFileSizeKb) {
            collected.push({ path: fullPath, skipped: true, reason: `حجم ${sizeKb.toFixed(0)} KB > ${opts.maxFileSizeKb} KB` });
            continue;
        }

        collected.push({ path: fullPath, skipped: false, sizeKb });
    }

    return collected;
}

// ─── ساخت محتوای متنی ──────────────────────────────────────────────────────────

function buildTextContent(inputPath, files) {
    const serviceName = path.basename(inputPath);
    const now = new Date().toLocaleString('fa-IR');
    const lines = [];

    lines.push('='.repeat(100));
    lines.push(`📦 سرویس: ${serviceName}`);
    lines.push(`📅 تاریخ: ${now}`);
    lines.push(`📂 مسیر: ${inputPath}`);
    lines.push(`📊 فایل‌های یافت شده: ${files.filter(f => !f.skipped).length} | رد شده: ${files.filter(f => f.skipped).length}`);
    lines.push('='.repeat(100));
    lines.push('');

    // لیست فایل‌های رد شده
    const skipped = files.filter(f => f.skipped);
    if (skipped.length > 0) {
        lines.push('⚠️ فایل‌های رد شده (حجم زیاد):');
        for (const f of skipped) {
            lines.push(`   ❌ ${path.relative(inputPath, f.path)} — ${f.reason}`);
        }
        lines.push('');
    }

    // محتوای فایل‌ها
    const included = files.filter(f => !f.skipped);
    for (const file of included) {
        const relativePath = path.relative(inputPath, file.path);
        lines.push('='.repeat(80));
        lines.push(`📄 ${relativePath}`);
        lines.push('='.repeat(80));
        lines.push('');

        try {
            const content = fs.readFileSync(file.path, 'utf8');
            lines.push(content);
        } catch (err) {
            lines.push(`⚠️ خطا در خواندن فایل: ${err.message}`);
        }

        lines.push('');
    }

    lines.push('='.repeat(100));
    lines.push(`🏁 پایان — ${serviceName}`);
    lines.push('='.repeat(100));

    return lines.join('\n');
}

// ─── ذخیره خروجی ───────────────────────────────────────────────────────────────

function saveOutput(text, outFile, compress) {
    const buffer = Buffer.from(text, 'utf8');

    if (compress) {
        const compressed = zlib.gzipSync(buffer, { level: 9 });
        fs.writeFileSync(outFile, compressed);
        return { originalSize: buffer.length, finalSize: compressed.length };
    } else {
        fs.writeFileSync(outFile, buffer);
        return { originalSize: buffer.length, finalSize: buffer.length };
    }
}

function formatSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}

// ─── اجرا ──────────────────────────────────────────────────────────────────────

function main() {
    const opts = parseArgs();

    // بررسی وجود پوشه
    if (!fs.existsSync(opts.inputPath)) {
        console.error(`❌ پوشه وجود ندارد: ${opts.inputPath}`);
        process.exit(1);
    }

    const stat = fs.statSync(opts.inputPath);
    if (!stat.isDirectory()) {
        console.error(`❌ مسیر داده شده پوشه نیست: ${opts.inputPath}`);
        process.exit(1);
    }

    // تعیین مسیر خروجی
    const serviceName = path.basename(opts.inputPath);
    const ext = opts.compress ? '.txt.gz' : '.txt';
    const outFile = opts.outFile || path.join(path.dirname(opts.inputPath), `${serviceName}_source${ext}`);

    console.log(`\n🔍 در حال پیمایش: ${opts.inputPath}`);
    console.log(`📁 پسوندهای هدف: ${[...opts.extensions].join(', ')}`);
    console.log(`🚫 پوشه‌های نادیده: ${[...opts.ignoreDirs].join(', ')}`);
    console.log(`📏 حداکثر سایز هر فایل: ${opts.maxFileSizeKb} KB\n`);

    // جمع‌آوری فایل‌ها
    const files = walkDir(opts.inputPath, opts);

    console.log(`✅ فایل‌های پردازش می‌شوند: ${files.filter(f => !f.skipped).length}`);
    if (files.filter(f => f.skipped).length > 0) {
        console.log(`⚠️  فایل‌های رد شده: ${files.filter(f => f.skipped).length}`);
    }

    // ساخت محتوا
    console.log(`\n📝 در حال ساخت محتوا...`);
    const text = buildTextContent(opts.inputPath, files);

    // ذخیره
    console.log(`${opts.compress ? '🗜️  در حال فشرده‌سازی' : '💾 در حال ذخیره'}...`);
    const sizes = saveOutput(text, outFile, opts.compress);

    console.log(`\n${'='.repeat(60)}`);
    console.log(`✅ ذخیره شد: ${outFile}`);
    console.log(`📊 سایز اصلی:    ${formatSize(sizes.originalSize)}`);
    if (opts.compress) {
        const ratio = ((1 - sizes.finalSize / sizes.originalSize) * 100).toFixed(1);
        console.log(`🗜️  سایز فشرده:   ${formatSize(sizes.finalSize)} (${ratio}% کاهش)`);
    }
    console.log(`${'='.repeat(60)}\n`);

    // نمایش لیست فایل‌ها
    console.log('📋 فایل‌های پردازش شده:');
    for (const f of files.filter(f => !f.skipped)) {
        console.log(`   ✅ ${path.relative(opts.inputPath, f.path)} (${f.sizeKb.toFixed(1)} KB)`);
    }
    for (const f of files.filter(f => f.skipped)) {
        console.log(`   ❌ ${path.relative(opts.inputPath, f.path)} — رد شد: ${f.reason}`);
    }

    console.log(`\n🎯 فایل آماده ارسال: ${outFile}`);

    if (opts.compress) {
        console.log(`\n💡 برای خواندن فایل فشرده:`);
        console.log(`   PowerShell: Expand-Archive یا [IO.File]::ReadAllText`);
        console.log(`   Linux/Mac:  gunzip -c ${path.basename(outFile)}`);
    }
}

main();