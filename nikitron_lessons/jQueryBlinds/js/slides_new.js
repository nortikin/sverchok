


function animate(tagId,alfa,step){
 div = document.getElementById(tagId);
 var items = new Array();
 //Выбираем все рисунки слайдшоу
 for(c=i=0;i<div.childNodes.length;i++){
  if (div.childNodes[i].tagName=="IMG"){
   items[c] = div.childNodes[i];
   c++;
  }
 }
 last = items[items.length-1];
 next = items[items.length-2];
 //делаем верхний в стопке(текущий) рисунок более прозрачным
 last.style.opacity= alfa/100;
 last.style.filter= "progid:DXImageTransform.Microsoft.Alpha(opacity="+alfa+")";
 last.style.filter= "alpha(opacity="+alfa+")";

 if ((alfa-step)>0){
  //если еще не достигли полной прозрачности верхнего рисунка - продолжаем анимацию
   setTimeout("animate('"+tagId+"',"+(alfa-step)+","+step+");",50);
 }else{
  //если достигли полной прозрачности верхнего рисунка
  //делаем абсолютно непрозрачным следующий рисунок
  next.style.opacity= 1;
  next.style.filter= "progid:DXImageTransform.Microsoft.Alpha(opacity=100)";
  next.style.filter= "alpha(opacity=100)";
  // а верхний рисунок перемещаем в низ стопки
  tmp = last;
  div.removeChild(last);
  div.insertBefore(tmp,items[0]);
  tmp.style.opacity= 1;
  tmp.style.filter= "progid:DXImageTransform.Microsoft.Alpha(opacity=100)";
  tmp.style.filter= "alpha(opacity=100)";

  setTimeout( "slideSwitch('"+tagId+"',1000)", 5000 );
 }
}
//эта функция делает видимым блок с рисунками для слайдшоу (изначально он невидим, чтобы избежать мерцания во время загрузки картинок) и запускает анимацию
function slideSwitch(tagId,speed){
 div = document.getElementById('slideshow');
 if (div.style.visibility!="visible"){
      div.style.visibility = "visible";
 }
 items = div.getElementsByTagName('img');
 if (items.length>0){
  animate(tagId,100,10);
 }
}
//выжидаем пару секунд, чтобы картинки успели загрузиться... можно просто поставить на onload-событие последнего из рисунков
setTimeout( "slideSwitch('slideshow',1000);",2000 );
