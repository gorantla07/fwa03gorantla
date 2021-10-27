var express = require('express');
var router = express.Router();
//var value=Math.random;

/* GET users listing. */
router.get('/', function (req, res, next) {
    fake_url = "https://fake.com/path" + req.url
    const url = new URL(fake_url)
    const search_params = url.searchParams
    if (req.method === 'GET') {
        var value = search_params.get("x");
        if(value === null)
        {
            value=Math.round(Math.random()*900);
        }
        console.log(value);
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.write('<br/>Math.acos() applied to ' + value + ' is ' + Math.cos(value))
        res.write('<br/>Math.sin() applied to ' + value + ' is ' + Math.asin(value))
        res.write('<br/>Math.sinh() applied to ' + value + ' is ' + Math.asinh(value))
        res.end()
    }
});

module.exports = router;