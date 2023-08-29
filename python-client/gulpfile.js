const gulp = require('gulp');
const postcss = require('gulp-postcss');
var concat = require('gulp-concat');
const babel = require("gulp-babel");
const minify = require('gulp-minify');


function scan_widget_css(cb) {
    gulp.src('./src/scan-widget/style.css')
        .pipe(postcss())
        .pipe(gulp.dest('./giskard/visualization/templates/scan_report/html/static/'));
    cb();
}

function scan_widget_js_external(cb) {
    gulp.src('./src/scan-widget/external-js/*.js')
        .pipe(babel({
            presets: ["@babel/preset-env"]
        }))
        .pipe(concat('external.js'))
        .pipe(gulp.dest('./giskard/visualization/templates/scan_report/html/static/'));
    cb();
}

function scan_widget_js_internal(cb) {
    gulp.src([
        './src/scan-widget/internal-js/iframeResizer.contentWindow.min.js',
        './src/scan-widget/internal-js/highlight.min.js',
        './src/scan-widget/internal-js/highlightjs-copy.min.js',
        './src/scan-widget/internal-js/scan.js',
    ])
        .pipe(babel({
            presets: ["@babel/preset-env"]
        }))
        .pipe(concat('internal.js'))
        .pipe(minify({ noSource: true, ext: { min: '.js' } }))
        .pipe(gulp.dest('./giskard/visualization/templates/scan_report/html/static/'));

    cb();
}

const scan_widget = gulp.parallel(scan_widget_css, scan_widget_js_external, scan_widget_js_internal);

exports.scan_widget = scan_widget;
exports.default = function () {
    gulp.watch('./giskard/visualization/templates/scan_report/*.html', scan_widget);
    gulp.watch('./src/scan-widget/*.html', scan_widget);
    gulp.watch('./src/scan-widget/*.js', scan_widget);
}