#!/usr/bin/env node

'use strict';

var fs = require('fs');
var coveralls = require('coveralls');

var argv = require('yargs').demand(2).argv._;

var fname = argv[0];
var basepath = argv[1];
var lcov = fs.readFileSync(fname).toString();

coveralls.convertLcovToCoveralls(lcov, {filepath: basepath}, function (err, data)
{
    if (err)
    {
        console.error(err);
        process.exit(1);
    }
    else
    {
        process.stdout.write(JSON.stringify(data));
        process.exit(0);
    }
});
