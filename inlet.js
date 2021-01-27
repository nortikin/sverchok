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

var gh_asset_https = "images/"

var context = {
  header: "Sverchok",
  menu_items: [
    {name:"About", link: ""},
    {name:"Gallery", link: ""},
    {name:"Download", link: ""},
    {name:"Manual", link: ""},
    {name:"Video",link: ""},
    {name:"Lessons", link: ""},
    {name:"Donate", link: ""}
  ]
}


// ------ html generation --------

var content_display = d3.select("#display")
  .style({background: '#051025'})
// -- dbdadb -- color old

var cmain = content_display.append("div")
  .classed("content_main", true);


function draw_content(){
  
  var maindiv = cmain.append('div').classed('sv_maindiv', true);
  var div1 = maindiv.append("div").classed("sv_header", true);
  var div2 = maindiv.append("div").classed("sv_menu", true);
  var div3 = maindiv.append("div").classed("sv_content", true);
  var div4 = div3.append('div').classed("sv_html", true);
  
  // this can be transitioned to other images using a timer.
  var header_image = "title.jpg"
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

function get_url_page(lpath) {
    var lmatch = lpath.match(/sverchok\/([^&]*)/);
    var pagename = "About";  // a default
    if (lmatch) {
        pagename = lmatch[1]
    }
    return pagename;
}

// This only actuates after the DOM content is loaded, and the
// URL  location contains a hash symbol. This event should occur by 
// - a refresh 
// - a hotlink to a section (ie sending a user to ".../sverchok/#Download" )
document.addEventListener("DOMContentLoaded", function(event) { 

    var thash = window.location.hash;
    if (thash) {
        console.log(thash);
        var pagename = thash.slice(1);
        var obtained_html = read_content(pagename + '.md');
        d3.select("div.sv_html").html(obtained_html);
    }
});
