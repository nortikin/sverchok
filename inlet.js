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
    {name:"About", link: "url"},
    {name:"Gallery", link: "urlo"},
    {name:"Download", link: "url"},
    {name:"Manual", link: "...url to manual..."},
    {name:"Lessons", link: "url"},
    {name:"Donate", link: "url"}
  ]
  ,  
  Sverchok: "\
<h3>Sverchok</h3>\
<img src='http://nikitron.cc.ua/sverch/skyscreapersm.jpg' />"
  ,
  
  Manual: "\
<h3>Manual</h3>\
<p>\
Read Sverchok documentation online <b>here</b><br> \
Download for offline referencing from <b>this link</b>.</p>"
  ,
  
  Lessons: "\
<h3>Lessons</h3>\
<p>\
Learn lessons.\
</p>"
  ,


  Gallery: "\
<h3>Gallery</h3>\
<p>\
werwer 23 23443 wer \
werwer wer werrree wet\
</p>"
  ,
  
  Download: "\
<h3>Download</h3>\
<p>\
Sverchok development is hosted on GitHub \
werwer wer werrree wet\
</p>"
  
}


// ------ html generation --------

var content_display = d3.select("#display")
  .style({background: '#555555'})

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
  div1.style({
    "background-image": url(gh_asset_https, header_image)
  })
      
  var menu = div2.selectAll("div")
    .data(context.menu_items)
    .classed("menu_item", true);
    
  var menu_divs = menu.enter().append("div").classed('item', true)
  menu_divs.append("text")
    .text(function(d, i) { return d.name })
    .classed("noselect", true);
  
  div4.html(context.Sverchok)
  
  menu.each(function(d){
    var obj = d3.select(this);
    
    // obj.on("mouseover", function(d){
    //   console.log('over', d.name);
    // })
    // obj.on("mouseout", function(d){
    //   console.log('out', d.name);
    // })    
    obj.on("click", function(d){
      console.log('clicked', d.name);
    
      if (d.name === 'Manual'){
          var obtained_html = read_content("Manual.md");
          div4.html(obtained_html);
      } 
      else if (d.name === 'Download'){
          var obtained_html = read_content("Download.md");
          div4.html(obtained_html);
      } 
      else if (d.name === 'About'){
          var obtained_html = read_content("About.md");
          div4.html(obtained_html);
      } 
      else if (d.name === 'Lessons'){
          var obtained_html = read_content("Lessons.md");
          div4.html(obtained_html);
      } 
      else if (d.name === 'Donate'){
          var obtained_html = read_content("Donate.md");
          div4.html(obtained_html);
      } 
      else if (d.name === 'Gallery'){
          var obtained_html = read_content("Gallery.md");
          div4.html(obtained_html);
      } 
      else {
          div4.html(context[d.name]);
      }
      
    })    
  })
}

draw_content()
