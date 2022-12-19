	(function($){
		$.fn.styleddropdown = function(){
			return this.each(function(){
				obj = $(this)
				obj.find('.field').click(function() { //onclick event, 'list' fadein
				obj.find('.list').fadeIn(400);
				
				$(document).keyup(function(event) { //keypress event, fadeout on 'escape'
					if(event.keyCode == 27) {
					obj.find('.list').fadeOut(400);
					}
				});
				
				obj.find('.list').hover(function(){ },
					function(){
						$(this).fadeOut(400);
					});
				});
				
				obj.find('.list li').click(function() { //onclick event, change field value with selected 'list' item and fadeout 'list'
				obj.find('.field')
					.val($(this).html())
					.css({
						'background':'#222',
						'color':'#fff'
					});
				obj.find('.list').fadeOut(400);
				});
			});
		};
	})(jQuery);

	$(function(){
		$('.size').styleddropdown();
	});
