def mediant(frac1, frac2):
    """Returns the mediant (n1+n2)/(d1+d2) of the two fractions, represented as a 2-tuple (n,d).
    frac1 and frac2 are given as 2-tuples (n,d)"""
    # print "%s m %s = %s" % (frac1, frac2, (frac1[0]+frac2[0], frac1[1]+frac2[1])
    return (frac1[0]+frac2[0], frac1[1]+frac2[1])

def compare_fracs(frac1, frac2, include_equal = False):
    """Return True if frac1 is greater than frac2."""
    if include_equal:
        return frac1[0]*frac2[1] >= frac2[0]*frac1[1]
    else:
        return frac1[0] * frac2[1] > frac2[0] * frac1[1]

class SBNode():
    """Represents one node in the Stern-Brocot tree"""
    
    def __init__(self, frac=(1,1), is_left_child=True, parent=None):
        self.parent = parent # the node this stems from. None if the top of the tree.
        self.frac = frac # the fraction at this node
        self.is_left_child = is_left_child # which side of the tree this is on

        self.left_child = None  # will be SBNode objects representing the object beneath this in the tree
        self.right_child = None

    def get_left_frac(self):
        """returns the existing fraction immediately to the left of this one"""
        if self.parent == None:
            # if this is the root node
            return (0,1)
        elif self.is_left_child:
            # if the left side, run up the tree until we find a right child
            return self.parent.get_left_frac()
        else:
            # if right child, just return the fraction above it
            return self.parent.frac

    def get_right_frac(self):
        """returns the fraction immediately to the right of this one"""
        if self.parent == None:
            # if this is the root node
            return (1,0)
        elif self.is_left_child:
            # if the left side, just return the fraction above it
            return self.parent.frac
        else:
            # if right child, run up the tree til we find a left child
            return self.parent.get_right_frac()

    def find_next_fraction (self, trg_frac, insert_after = True):
        #print ("Current node: " + str(self.frac[0]) + "/" + str(self.frac[1]))
        if self.frac == trg_frac:
            #print ("Trg frac found - retreiving child")
            if insert_after:
                #get right child
                child_frac = mediant(self.frac, self.get_right_frac())
                self.right_child = SBNode(frac=child_frac, is_left_child=False, parent=self)
                
            else:
                #get left child
                child_frac = mediant(self.frac, self.get_left_frac())
                self.left_child = SBNode(frac=child_frac, is_left_child=True, parent=self)
                
            #print ("New fraction: " + str(child_frac[0]) + "/" + str(child_frac[1]))
            return child_frac
        
        elif compare_fracs(trg_frac, self.frac):
        #True if target fraction is higher than current fraction
            #print ("Target fraction is bigger - go right")
            #get the RIGHT child fraction
            child_frac = mediant(self.frac, self.get_right_frac())
            self.right_child = SBNode(frac=child_frac, is_left_child=False, parent=self)
            return self.right_child.find_next_fraction(trg_frac, insert_after)

        else:
            #print ("Target fraction is smaller - go left")
            #get the LEFT child fraction
            child_frac = mediant(self.frac, self.get_left_frac())
            self.left_child = SBNode(frac=child_frac, is_left_child=True, parent=self)
            return self.left_child.find_next_fraction(trg_frac, insert_after)



    def find_intermediate_fraction(self, lower_frac, upper_frac):
        if compare_fracs(self.frac, lower_frac):
            if compare_fracs(self.frac, upper_frac, True):
                #get the left child fraction
                child_frac = mediant(self.frac, self.get_left_frac())
                self.left_child = SBNode(frac=child_frac, is_left_child=True, parent=self)
                return self.left_child.find_intermediate_fraction(lower_frac, upper_frac)
            else:
                return self.frac
        else:
            #get the right child fraction
            child_frac = mediant(self.frac, self.get_right_frac())
            self.right_child = SBNode(frac=child_frac, is_left_child=False, parent=self)
            return self.right_child.find_intermediate_fraction(lower_frac, upper_frac)
