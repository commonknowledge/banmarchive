!function(){"use strict";var n={41890:function(n,t,e){var r=this&&this.__importDefault||function(n){return n&&n.__esModule?n:{default:n}};t.__esModule=!0;var o=r(e(73609));window.buildExpandingFormset=function(n,t){void 0===t&&(t={});var e=o.default("#"+n+"-ADD"),r=o.default("#"+n+"-FORMS"),i=o.default("#"+n+"-TOTAL_FORMS"),u=parseInt(i.val(),10);if(t.onInit)for(var a=0;a<u;a++)t.onInit(a);var l=document.getElementById(n+"-EMPTY_FORM_TEMPLATE");l.innerText?l=l.innerText:l.textContent&&(l=l.textContent),e.on("click",(function(){if(e.hasClass("disabled"))return!1;var n=l.replace(/__prefix__/g,u).replace(/<-(-*)\/script>/g,"<$1/script>");r.append(n),t.onAdd&&t.onAdd(u),t.onInit&&t.onInit(u),u++,i.val(u)}))}},73609:function(n){n.exports=jQuery}},t={};function e(r){if(t[r])return t[r].exports;var o=t[r]={id:r,loaded:!1,exports:{}};return n[r].call(o.exports,o,o.exports,e),o.loaded=!0,o.exports}e.m=n,e.x=function(){},e.n=function(n){var t=n&&n.__esModule?function(){return n.default}:function(){return n};return e.d(t,{a:t}),t},e.d=function(n,t){for(var r in t)e.o(t,r)&&!e.o(n,r)&&Object.defineProperty(n,r,{enumerable:!0,get:t[r]})},e.g=function(){if("object"==typeof globalThis)return globalThis;try{return this||new Function("return this")()}catch(n){if("object"==typeof window)return window}}(),e.hmd=function(n){return(n=Object.create(n)).children||(n.children=[]),Object.defineProperty(n,"exports",{enumerable:!0,set:function(){throw new Error("ES Modules may not assign module.exports or exports.*, Use ESM export syntax, instead: "+n.id)}}),n},e.o=function(n,t){return Object.prototype.hasOwnProperty.call(n,t)},e.r=function(n){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(n,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(n,"__esModule",{value:!0})},e.j=276,function(){var n={276:0},t=[[41890,751],[90971,751]],r=function(){},o=function(o,i){for(var u,a,l=i[0],f=i[1],c=i[2],d=i[3],s=0,p=[];s<l.length;s++)a=l[s],e.o(n,a)&&n[a]&&p.push(n[a][0]),n[a]=0;for(u in f)e.o(f,u)&&(e.m[u]=f[u]);for(c&&c(e),o&&o(i);p.length;)p.shift()();return d&&t.push.apply(t,d),r()},i=self.webpackChunkwagtail=self.webpackChunkwagtail||[];function u(){for(var r,o=0;o<t.length;o++){for(var i=t[o],u=!0,a=1;a<i.length;a++){var l=i[a];0!==n[l]&&(u=!1)}u&&(t.splice(o--,1),r=e(e.s=i[0]))}return 0===t.length&&(e.x(),e.x=function(){}),r}i.forEach(o.bind(null,0)),i.push=o.bind(null,i.push.bind(i));var a=e.x;e.x=function(){return e.x=a||function(){},(r=u)()}}(),e.x()}();
//# sourceMappingURL=expanding_formset.js.map