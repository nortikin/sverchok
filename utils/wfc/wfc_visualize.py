"Visualize the patterns into tiles and so on."

import numpy as np


def tile_grid_to_image(tile_grid, tile_catalog, tile_size, visualize=False, partial=False, color_channels=3):
    """
    Takes a tile_grid and transforms it into an image, using the information
    in tile_catalog. We use tile_size to figure out the size the new image
    should be, and visualize for displaying partial tile patterns.
    """
    new_img = np.zeros((tile_grid.shape[0] * tile_size[0], tile_grid.shape[1] * tile_size[1], color_channels), dtype=np.int64)
    if partial and (len(tile_grid.shape)) > 2:
        # TODO: implement rendering partially completed solution
        # Call tile_grid_to_average() instead.
        assert False
    else:
        for i in range(tile_grid.shape[0]):
            for j in range(tile_grid.shape[1]):
                tile = tile_grid[i,j]
                for u in range(tile_size[0]):
                    for v in range(tile_size[1]):
                        pixel = [200, 0, 200]
                        ## If we want to display a partial pattern, it is helpful to
                        ## be able to show empty cells. Therefore, in visualize mode,
                        ## we use -1 as a magic number for a non-existant tile.
                        if visualize and ((-1 == tile) or (-2 == tile)):
                            if (-1 == tile):
                                if 0 == (i + j) % 2:
                                    pixel = [255, 0, 255]
                            if (-2 == tile):
                                pixel = [0, 255, 255]
                        else:
                            pixel = tile_catalog[tile][u,v]
                        # TODO: will need to change if using an image with more than 3 channels
                        new_img[(i * tile_size[0]) + u, (j * tile_size[1]) + v] = np.resize(pixel, new_img[(i * tile_size[0]) + u, (j * tile_size[1]) + v].shape)
    return new_img
