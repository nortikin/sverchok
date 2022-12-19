/*!
 * jQuery Blinds
 * http://www.littlewebthings.com/projects/blinds
 *
 * Copyright 2010, Vassilis Dourdounis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */
(function($){

	$.fn.blinds = function (options) {

		$(this).find('li').hide();
		$(this).addClass('blinds_slideshow');

		settings = {};
		settings.tile_orchestration = this.tile_orchestration;

		settings.h_res = 12;
		settings.v_res = 1;

		settings.width = $(this).find('li:first').width();
		settings.height = $(this).find('li:first').height();

		jQuery.extend(settings, options);

		tiles_width = settings.width / settings.h_res;
		tiles_height = settings.height / settings.v_res;

		// Get image list
		blinds_images = [];
		$(this).find('img').each(function (i, e) {
			blinds_images[blinds_images.length] = {'title': e.alt, 'src': e.src}
		});

		// Create blinds_container
		$(this).append('<div class="blinds_container"></div>');

		blinds_container = $(this).find('.blinds_container');
		blinds_container.css({
			'position'	: 'relative', 
			'display'	: 'block', 
			'width'		: settings.width, 
			'height'	: settings.height, 
//			'border'	: '1px solid red', // debuging
			'background': 'transparent url("' + blinds_images[1]['src'] + '") 0px 0px no-repeat'
		} );
		// Setup tiles
		for (i = 0; i < settings.h_res; i++)
		{
			for (j = 0; j < settings.v_res; j++)
			{
				if (tile = $(this).find('.tile_' + i + '_' + j))
				{
					h = '<div class="outer_tile_' + i + '_' + j + '"><div class="tile_' + i + '_' + j + '"></div></div>';
					blinds_container.append(h);
					outer_tile = $(this).find('.outer_tile_' + i + '_' + j);
					outer_tile.css({
						'position'	: 'absolute',
						'width'		: tiles_width,
						'height'	: tiles_height,
						'left'		: i * tiles_width,
						'top'		: j * tiles_height
					})

					tile = $(this).find('.tile_' + i + '_' + j);
					tile.css({
						'position'	: 'absolute',
						'width'		: tiles_width,
						'height'	: tiles_height,
						'left'		: 0,
						'top'		: 0,
//						'border'	: '1px solid red', // debuging
						'background': 'transparent url("' + blinds_images[0]['src'] + '") -' + (i * tiles_width) + 'px -' + (j * tiles_height) + 'px no-repeat' 
					})
					
					jQuery.data($(tile)[0], 'blinds_position', {'i': i, 'j': j});
				}
			}
		}

		jQuery.data(this[0], 'blinds_config', {
			'h_res': settings.h_res,
			'v_res': settings.v_res,
			'tiles_width': tiles_width,
			'tiles_height': tiles_height,
			'images': blinds_images,
			'img_index': 0,
			'change_buffer': 0,
			'tile_orchestration': settings.tile_orchestration
		});
	}
	
	$.fn.blinds_change = function (img_index) {

		// reset all sprites
		config = jQuery.data($(this)[0], 'blinds_config');
		for (i = 0; i < config.h_res; i++)
		{
			for (j = 0; j < config.v_res; j++) {
				$(this).find('.tile_' + i + '_' + j).show().css('background', 'transparent ' + 'url("' + config.images[config.img_index]['src'] + '") -' + (i * config.tiles_width) + 'px -' + (j * config.tiles_height) + 'px no-repeat');
			}
		}

		$(this).children('.blinds_container').css('background', 'transparent url("' + blinds_images[img_index]['src'] + '") 0px 0px no-repeat' );

		config.img_index = img_index;
		jQuery.data($(this)[0], 'blinds_config', config);

		for (i = 0; i < config.h_res; i++)
		{
			for (j = 0; j < config.v_res; j++) {
				t = config.tile_orchestration(i, j, config.h_res, config.v_res);
				
				config = jQuery.data($(this)[0], 'blinds_config');
				config.change_buffer = config.change_buffer + 1;
				jQuery.data(this[0], 'blinds_config', config);

				$(this).find('.tile_' + i + '_' + j).fadeOut(t, function() {
					blinds_pos = jQuery.data($(this)[0], 'blinds_position');
					config = jQuery.data($(this).parents('.blinds_slideshow')[0], 'blinds_config');

					$(this).css('background', 'transparent ' + 'url("' + config.images[config.img_index]['src'] + '") -' + (blinds_pos.i * config.tiles_width) + 'px -' + (blinds_pos.j * config.tiles_height) + 'px no-repeat');

					config.change_buffer = config.change_buffer - 1;
					jQuery.data($(this).parents('.blinds_slideshow')[0], 'blinds_config', config);

					if (config.change_buffer == 0) {
//						$(this).parent().parent().children().children().css('width', config.tiles_width);
						$(this).parent().parent().children().children().show();
					}

				});
			}
		}
	}

	$.fn.tile_orchestration = function (i, j, total_x, total_y) {
		return (Math.abs(i-total_x/2)+Math.abs(j-total_y/2))*100;
	}

})(jQuery);


