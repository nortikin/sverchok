/*
Prelim redesign of Sverchok landing page
-- been too long since I wrote .js and d3, 

page theme is purely accidental for shape visualization
*/

// ------- header background variables, setup and functions -----------

function url(prefix, str){
  return "url(" + prefix + str + ")";
}

function read_content(myUrl) {
  var result = null;
  $.ajax({
    url: myUrl, 
    type: 'get', 
    dataType: 'html',
    async: false,
    success: function(data) { result = data; } 
  });
  FileReady = true;

  var converter = new Showdown.converter();
  return converter.makeHtml(result);
}

var gh_asset_https = "https://cloud.githubusercontent.com/assets/"

var context = {
  header: "Sverchok",
  menu_items: [
    {name:"About", link: ""},
    {name:"Gallery", link: ""},
    {name:"Download", link: ""},
    {name:"Manual", link: ""},
    {name:"Video",link: ""},
    {name:"Lessons", link: ""},
    {name:"Magazines", link: ""},
    {name:"Donate", link: ""}
  ]
}


// ------ html generation --------

var content_display = d3.select("#display")
  .style({background: '#dbdadb'})

var cmain = content_display.append("div")
  .classed("content_main", true);


function draw_content(){
  
  var maindiv = cmain.append('div').classed('sv_maindiv', true);
  var div1 = maindiv.append("div").classed("sv_header", true);
  var div2 = maindiv.append("div").classed("sv_menu", true);
  var div3 = maindiv.append("div").classed("sv_content", true);
  var div4 = div3.append('div').classed("sv_html", true);
  
  // this can be transitioned to other images using a timer.
  var header_image = "619340/5299224/1c085d8e-7bc5-11e4-8246-6951c48014ef.png"
  div1.classed('sv_header_background', true).style({
    "background-image": url(gh_asset_https, header_image)
  })
      
  var menu = div2.selectAll("div")
    .data(context.menu_items)
    .classed("menu_item", true);
    
  var menu_divs = menu.enter().append("div").classed('item', true)
  menu_divs.append("text")
    .text(function(d, i) { return d.name })
    .classed("noselect", true);
  
  div4.html(read_content("About.md"))
  
  menu.each(function(d){
    var obj = d3.select(this);
    var _div4 = d3.select("div.sv_html");
    
    // obj.on("mouseover", function(d){
    // obj.on("mouseout", function(d){
    obj.on("click", function(d){
      var markdown_refname = d.name + ".md";
      var obtained_html = read_content(markdown_refname);
      _div4.html(obtained_html);
      history.pushState(null, null, d.name);
      // history.pushState(null, null, d.name);
      
    })    
  })
}

draw_content()

window.addEventListener("popstate", function(e) {
    var pagename = get_url_page(location.pathname)
    var _div4 = d3.select("div.sv_html");
    var obtained_html = read_content(pagename + '.md');
    _div4.html(obtained_html);
});

// window.addEventListener("hashchange", function(e) {
//     var thash = window.location.hash;
//     console.log(thash);
//     var pagename = thash.slice(1);
//     var _div4 = d3.select("div.sv_html");
//     var obtained_html = read_content(pagename + '.md');
//     _div4.html(obtained_html);

// }, false);

function get_url_page(lpath) {
    var lmatch = lpath.match(/sverchok\/([^&]*)/);
    var pagename = "About";  // a default
    if (lmatch) {
        pagename = lmatch[1]
    }
    return pagename;
}

document.addEventListener("DOMContentLoaded", function(event) { 
  //do work
    var thash = window.location.hash;
    if (thash) {
        console.log(thash);
    }
});