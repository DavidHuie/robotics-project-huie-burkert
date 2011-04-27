import cv

class RGBItem:
    def __init__(self, image):
        self.R = None
        self.G = None
        self.B = None
        self.image = image
        self.clicks = 0

    def register_coordinates(self, event, x, y, flags, param):
        if event != cv.CV_EVENT_LBUTTONDOWN:
            return

        self.clicks += 1

        b,g,r,_ = list(cv.Get2D(self.image, y, x))

        print "Point selected with RGB =", (r,g,b)

        if self.R is None:
            self.R = [r,r]
            self.G = [g,g]
            self.B = [b,b]
        else:
            for C, c in zip([self.R,self.G,self.B], [r,g,b]):
                if c < C[0]: C[0] = c
                elif c > C[1]: C[1] = c

    def get_clicks(self):
        return self.clicks

    def get_R(self): return self.R
    def get_G(self): return self.G
    def get_B(self): return self.B
    def get_RGB_ranges(self): return (self.R, self.G, self.B)

def get_item_rgb(image):
    item = RGBItem(image)

    window = "jeffIsDirty"
    
    cv.NamedWindow(window)
    cv.SetMouseCallback(window, item.register_coordinates)
    cv.ShowImage(window, image)

    

    print "Please select item as many times as possible. Press any key on the keyboard when finished."

    cv.WaitKey()

    print "Calibration finished."
    print "R:", item.get_R()
    print "G:", item.get_G()
    print "B:", item.get_B()

    cv.DestroyWindow(window)

    return item.get_RGB_ranges()
        
        


