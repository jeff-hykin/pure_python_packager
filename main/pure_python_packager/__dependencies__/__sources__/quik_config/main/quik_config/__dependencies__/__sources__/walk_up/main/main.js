let walkUpUntil
// 
// node.js
// 
if (typeof Deno == 'undefined') {
    const process = require("process")
    const path = require("path")
    const fs = require("fs")

    walkUpUntil = (fileToFind, startPath=null)=> {
        let here = startPath || process.cwd()
        if (!path.isAbsolute(here)) {
            here = path.join(process.cwd(), fileToFind)
        }
        while (1) {
            let checkPath = path.join(here, fileToFind)
            if (fs.existsSync(checkPath)) {
                return checkPath
            }
            // reached the top
            if (here == path.dirname(here)) {
                return null
            } else {
                // go up a folder
                here =  path.dirname(here)
            }
        }
    }
    
    module.exports = { walkUpUntil }
// 
// Deno (copy-pase)
// 
} else {
    console.error("sorry deno doesn't work yet, the code is there its just the import/export stuff breaking it")
    const Path = import("https://deno.land/std@0.117.0/path/mod.ts")

    walkUpUntil = async (fileToFind, startPath=null)=> {
        await Path
        const cwd = Deno.cwd()
        let here = startPath || cwd
        if (!Path.isAbsolute(here)) {
            here = Path.join(cwd, fileToFind)
        }
        while (1) {
            let checkPath = Path.join(here, fileToFind)
            const pathInfo = await Deno.stat(checkPath).catch(()=>({doesntExist: true}))
            if (!pathInfo.doesntExist) {
                return checkPath
            }
            // reached the top
            if (here == Path.dirname(here)) {
                return null
            } else {
                // go up a folder
                here =  Path.dirname(here)
            }
        }
    }
}

