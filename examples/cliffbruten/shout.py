

class Shout:
    def __init__(self,parent,kind):
        self.parent = parent
        self.price = self.parent.p
        self.kind = kind 
        self.accepted = False
        
    def __repr__(self):
        return "<SHOUT %s %s %s>" % (self.price, self.parent, self.kind)