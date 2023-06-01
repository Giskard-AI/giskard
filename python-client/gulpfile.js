const gulp = require('gulp');
const postcss = require('gulp-postcss');
var concat = require('gulp-concat');
const babel = require("gulp-babel");
const minify = require('gulp-minify');

gulp.task('widget-css', function () {
    return gulp.src('./src/scan-widget/style.css')
        .pipe(postcss())
        .pipe(gulp.dest('./giskard/scanner/templates/static/'));
});

gulp.task('widget-js-external', function () {
    return gulp.src('./src/scan-widget/external-js/*.js')
        .pipe(babel({
            presets: ["@babel/preset-env"]
        }))
        .pipe(concat('external.js'))
        .pipe(gulp.dest('./giskard/scanner/templates/static/'));
})

gulp.task('widget-js-internal', function () {
    return gulp.src([
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
        .pipe(gulp.dest('./giskard/scanner/templates/static/'));
})

gulp.task('widget', gulp.parallel('widget-css', 'widget-js-internal', 'widget-js-external'));