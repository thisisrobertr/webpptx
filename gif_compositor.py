import PIL.Image # not included; pip3 install pillow
import io
import time
import os


class GIFContainer:
    def __init__(self, buf, filename, x, y, w, h):
        self.buf = buf
        self.filename = filename
        self.img = PIL.Image.open(io.BytesIO(buf))  # doing this with BytesIO greatly reduces the required quantity of temp files
        self.x = x
        self.y = y
        self.width = w
        self.height = h
        self.max_index = self.img.n_frames  # length of the GIF, in frames
        self.framerate_normalization_factor = 1  # stores how many overall frames should be rendered before advancing this GIF.
        self.framedelay = self.img.info['duration']  # makes delay more conveniently available, primarily for the benefit of the lambda function as the key in sorted()
        
    def scaleXPosition(self, factor):
        self.x = int(self.x * factor)
        
    def scaleYPosition(self, factor):
        self.y = int(self.y * factor)
        
    def scaleWidth(self, factor):
        self.width = int(self.width * factor)

    def scaleHeight(self, factor):
        self.height = int(self.height * factor)

def compose_gifs(image_file, gif_data, result_file, frame_count):
    # When I first wrote this, I didn't account for that fact that GIFs can have custom and variable framerates (this is expressed not in frames per second, but in delay between frames;
    # I believe the unit is milliseconds). I didn't address the latter of those issues, but the former one is now less of a problem.
    # GIFs that are markedly slower (flowcharts, for example) will have the same frame drawn multiple times while faster animations advance. The array supplied in gifs_data is already sorted by framerate;
    # that's done when the web server processes the API request. 
    for i in gif_data:
        i.framerate_normalization_factor = i.framedelay // gif_data[0].framedelay  # Determine how many times slower the current GIF is than the fastest (first) one. Use floor division to avoid decimal framerates
        if i.max_index * i.framerate_normalization_factor > frame_count:  
            frame_count = i.framerate_normalization_factor * i.max_index  # If adjusting for framerate would increase the length of the slide's overall GIF, notice and prepare that here by adjusting frame_count

    # Compose a GIF onto a still image
    to_delete = []  # stores files scheduled for deletion
    frames = []  # Stores each frame of each animated slide.
    for i in range(frame_count):
        frames.append(PIL.Image.open(image_file))  # create new copy of the initial image for this frame
        frames[i] = frames[i].convert('RGB')  # Keep everything in RGB mode so pasting works correctly. Transparency doesn't work, so don't use an alpha channel.
        idx = 0  # I need the index but having the object from a foreach is more concise.
        for j in gif_data:
            gif = PIL.Image.open(io.BytesIO(j.buf))
            if i < j.max_index * j.framerate_normalization_factor:  
                gif.seek(i // j.framerate_normalization_factor)  # Slow animations only advance every few frames, as set by framerate_normalization_factor
            else:  # If this is shorter than the longest GIF file, use the last frame and do not seek past the end.
                gif.seek(j.max_index-1)
                
            #tmp = gif
            gif = gif.convert('RGB')
            gif = gif.resize((j.width, j.height))  # Scale to fit
            w, h = gif.size
            frames[i].paste(gif, (j.x, j.y, j.x+w, j.y+h))  # Add this frame to the main slide
            idx += 1

        del idx  # not out of scope as it would be a normal for loop. Consequently, it may not be deallocated automatically- I do this explicitly just to be sure(r)
    
    # clean up temporary files
    for i in to_delete:
        os.remove(i)

    # create composite gif for response. To paraphrase Bill Gates, 32767 loops ought to be enough for anybody. Use the shortest delay to set framerate- the first item in gif_data.
    frames[0].save(result_file, save_all=True, append_images=frames[1:], loop=32767, duration=gif_data[0].framedelay)  
