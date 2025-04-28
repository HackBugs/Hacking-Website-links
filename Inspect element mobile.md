> Subscribe My channel for More Hacking tips and tricks ke liye.
> Channel - [HackBugs](https://www.youtube.com/hackbugs)
## Enable Inspect Element in mobile phone 

```
javascript:(function () {
    var script =  document.createElement('script');
    script.src="//cdn.jsdelivr.net/npm/eruda";
    document.body.appendChild(script);
    script.onload = function () {
        eruda.init()
    }
})();
```

## Use this code on developer tool console to edit website

```
document.body.contentEditable = true
```
