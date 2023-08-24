const gulp = require('gulp');
const postcss = require('gulp-postcss');
var concat = require('gulp-concat');
const babel = require("gulp-babel");
const minify = require('gulp-minify');


function widget_css(cb) {
    gulp.src('./src/scan-widget/style.css')
        .pipe(postcss())
        .pipe(gulp.dest('./giskard/visualization/templates/static/'));
    cb();
}

function widget_js_external(cb) {
    gulp.src('./src/scan-widget/external-js/*.js')
        .pipe(babel({
            presets: ["@babel/preset-env"]
        }))
        .pipe(concat('external.js'))
        .pipe(gulp.dest('./giskard/visualization/templates/static/'));
    cb();
}

function widget_js_internal(cb) {
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
        .pipe(gulp.dest('./giskard/visualization/templates/static/'));

    cb();
}

const widget = gulp.parallel(widget_css, widget_js_external, widget_js_internal);

exports.widget = widget;
exports.default = function () {
    gulp.watch('./giskard/visualization/templates/*.html', widget);
    gulp.watch('./src/scan-widget/*.html', widget);
    gulp.watch('./src/scan-widget/*.js', widget);
}