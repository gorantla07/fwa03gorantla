var express = require('express');
var router = express.Router();
value =0

/* GET users listing. */
router.get('/', function(req, res, next) {
  value=value+1
  res.send('user accesses are: '+value);
});

module.exports = router;
