$module = {
    __getattr__ : function(attr){
        if (attr == 'new') {return $hashlib_new;}
        return this[attr]
    },
    md5: function() {return $hashlib_new('md5')},
    sha1: function() {return $hashlib_new('sha1')},
    sha224: function() {return $hashlib_new('sha224')},
    sha256: function() {return $hashlib_new('sha256')},
    sha384: function() {return $hashlib_new('sha384')},
    sha512: function() {return $hashlib_new('sha512')},

    algorithms_guaranteed: ['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512'],
    algorithms_available:  ['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512']
}


//todo: eventually move this function to a "utility" file or use ajax module?
function $get_CryptoJS_lib(alg) {
   var imp=$importer()
   var $xmlhttp=imp[0], fake_qs=imp[1], timer=imp[2], res=null

   $xmlhttp.onreadystatechange = function(){
        if($xmlhttp.readyState==4){
            window.clearTimeout(timer)
            if($xmlhttp.status==200 || $xmlhttp.status==0){res=$xmlhttp.responseText}
            else{
                // don't throw an exception here, it will not be caught (issue #30)
                res = Error()
                res.name = 'NotFoundError'
                res.message = "No CryptoJS lib named '"+alg+"'"
            }
        }
   }

   $xmlhttp.open('GET', __BRYTHON__.brython_path+'libs/crypto_js/rollups/'+alg+'.js'+fake_qs,false)
   if('overrideMimeType' in $xmlhttp){$xmlhttp.overrideMimeType("text/plain")}
   $xmlhttp.send()
   if(res.constructor===Error){throw res} // module not found

   try{
      eval(res + "; __BRYTHON__.CryptoJS=CryptoJS;")
   } catch (err) { 
      throw Error("JS Eval Error", "Cannot eval CryptoJS algorithm '" + alg + "' : error:" + err);
   }
}

function $hashlib_new(alg) {
    if (alg == 'md5') {
       if (__BRYTHON__.Crypto === undefined || 
           __BRYTHON__.CryptoJS.algo.MD5 === undefined) $get_CryptoJS_lib('md5')
       this.hash = __BRYTHON__.CryptoJS.algo.MD5.create()
    } else if (alg == 'sha1') {
       if (__BRYTHON__.Crypto === undefined || 
           __BRYTHON__.CryptoJS.algo.SHA1 === undefined) $get_CryptoJS_lib('sha1')
       this.hash = __BRYTHON__.CryptoJS.algo.SHA1.create()
    } else if (alg == 'sha224') {
       if (__BRYTHON__.Crypto === undefined || 
           __BRYTHON__.CryptoJS.algo.SHA224 === undefined) $get_CryptoJS_lib('sha224')
       this.hash = __BRYTHON__.CryptoJS.algo.SHA224.create()
    } else if (alg == 'sha256') {
       if (__BRYTHON__.Crypto === undefined || 
           __BRYTHON__.CryptoJS.algo.SHA256 === undefined) $get_CryptoJS_lib('sha256')
       this.hash = __BRYTHON__.CryptoJS.algo.SHA256.create()
    } else if (alg == 'sha384') {
       if (__BRYTHON__.Crypto === undefined || 
           __BRYTHON__.CryptoJS.algo.SHA384 === undefined) $get_CryptoJS_lib('sha384')
       this.hash = __BRYTHON__.CryptoJS.algo.SHA384.create()
    } else if (alg == 'sha512') {
       if (__BRYTHON__.Crypto === undefined || 
           __BRYTHON__.CryptoJS.algo.SHA512 === undefined) $get_CryptoJS_lib('sha512')
       this.hash = __BRYTHON__.CryptoJS.algo.SHA512.create()
    } else {
       $raise('AttributeError', 'Invalid hash algorithm:' + alg)
    }
 
    this.__class__ = $type
    this.__getattr__ = function(attr){return $getattr(this,attr)}
    this.__str__ = function(){return this.hexdigest()}
    this.update = function(msg){this.hash.update(msg)}
    this.copy = function(){return this.hash.clone()}

    this.hexdigest = function() {
        var temp=this.hash.clone();
        temp=temp.finalize();
        return temp.toString();
    }

    return this;
}

$module.__class__ = $module
$module.__str__ = function() {return "<module 'hashlib'>"}
