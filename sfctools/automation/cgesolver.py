__version__ = "0.3"
__author__ = "Thomas Baldauf"
__email__ = "thomas.baldauf@dlr.de"
__license__ = "MIT"
__birthdate__ = '15.11.2021'
__status__ = 'dev' # options are: dev, test, prod

"""
This ships a functionality to analytically solve a CGE model using a
'production tree' approach. BETA has not yet been fully tested
"""

from sympy import *
import sys


def construct_prodfunc(entry,product,factors,learning):
    """
    constructs a linear production function 
    :param entry:  'linear' only one allowed currently
    :param product: str, what is produced by this agent?
    :param factors: list of str (length 2) what are the input factors?
    :param learning: learning: technological learning dict {product:learnin_coefficient}, i.e. is the input modified
    """
    
    if entry["type"] == "linear":
        coeffs = entry["coeffs"]

        symcoeffs = Matrix(len(coeffs),1,[Symbol(i) for i in coeffs])
        symfactors = Matrix(len(factors), 1, [Symbol(i) for i in factors])

        equation = sum([symcoeffs[i]* symfactors[i] for i in range(len(coeffs))]) - Symbol(product)
        if str(product) in learning:
            equation -= learning[str(product)]

        cond = str(sum(symcoeffs)) + "= 1"
        parameters = sum(symcoeffs) - 1

        unknowns = [Symbol(i) for i in factors] + [Symbol(product)]
        # unknowns += [i for i in symcoeffs]

        #print(equation)
        return equation,cond,unknowns,parameters


    else:
        raise NotImplementedError("Other than type 'linear' currently not possible.")



def construct_costfunc(entry,product,factors,learning):
    if entry["type"] == "linear":
        coeffs = entry["coeffs"]

        symcoeffs = Matrix(len(coeffs),1,[Symbol(i) for i in coeffs])
        symprices = Matrix(len(factors), 1, [Symbol("p_"+i) for i in factors])

        equation = sum([symcoeffs[i]* symprices[i] for i in range(len(coeffs))]) - Symbol("p_"+product)
        if str(product) in learning:
            equation += learning[str(product)]

        cond = str(sum(symcoeffs)) + "=1"
        parameters = sum(symcoeffs) - 1

        unknowns = [Symbol(i) for i in factors] + [Symbol(product)]
        # unknowns += [i for i in symcoeffs]

        return equation, cond, unknowns, parameters

    else:
        raise NotImplementedError("Other than type 'linear' currently not possible.")


def nextwait(s):
    d = {
        "/":"- ",
        "- ":"\\",
        "\\":"|",
        "|":"+",
        "+":"/"
    }
    return d[s]


def traverse(t, production_dict,learning, l=None,s = None,unknowns = None, abbrevs=None,topnode=None,wait="/",rec_depth=0):
    """
    traverses a tree
    :param t:  tree (nested dict)
    :param production_dict: production dict
    :param learning: dict storing improvements in technology

    :param l: recursion param, do not use , stores equations
    :param s: recursion param, do not use, stores equations for elasticities
    :param unknowns: recursion paramm, do not use
    :param topnode:  recursion param, do not use
    :param rec_depth: recursion depth
    :return:
    """

    # TODO make this more efficient

    if l is None: # stores equations
        l = []
    if unknowns is None: # stores unknowns
        unknowns = []
    if s is None:  # stores the equations for elasticities
        s = []
    if abbrevs is None: # stores abbreviations
        abbrevs = []

    # generate production and cost functions

    if topnode is not None:
        topnode_s = topnode.split(";")[0]
        unknowns.append(topnode_s)
        unknowns.append("p_" + topnode_s)

    for k,v in t.items(): # traverse sub-tree

        # has production parameters
        splitk = k.split(";")
        print("   "*rec_depth,"|__ visit",splitk[0],"    "*10)

        fact = splitk[0].strip()
        unknowns.append(fact)
        unknowns.append("p_"+fact)

        # production

        if len(splitk) > 1:  # has production parameters
            fact = splitk[0].strip()
            factors = [v.split(";")[0].strip() for v in v.keys()]

            prodfunc,cond1,unknowns1,parameters = construct_prodfunc(
                entry = production_dict[splitk[1].strip()],
                product = fact,
                factors = factors,
                learning=learning,
                )

            costfunc, cond2, unknowns2, parameters = construct_costfunc(
                entry=production_dict[splitk[1].strip()],
                product=fact,
                factors=factors,
                learning=learning)

            l.append(prodfunc)
            l.append(costfunc)

            abbrevs += [parameters]  # str(cond1))
            # abbrevs.append(parameters)  # str(cond2))

            for f in unknowns1+unknowns2:

                unknowns.append(f)
                #unknowns.append(Symbol("p_"+str(f)))

            if v != {} and len(v) > 1:
                print("   "*rec_depth," ___", " %i equations" % len(list(set(l))) )
                for l_i in list(set(l)):
                    print("   " * (1+rec_depth), "    ",l_i)

                new_vals = traverse(v, production_dict, learning, l.copy(), s.copy(), topnode=k, abbrevs=abbrevs, unknowns=unknowns, wait=wait, rec_depth=rec_depth+1)
                l += new_vals[0]
                unknowns += new_vals[1]

        else:  # has no production parameters

            if v != {}:
                if len(v.keys()) >= 1:
                    print("   "*rec_depth," ___", " %i equations" % len(list(set(l))) )
                    for l_i in list(set(l)):
                        print("   " * (1 + rec_depth), "    ", l_i)

                    new_vals = traverse(v, production_dict, learning, l.copy(), s.copy(), topnode=k, abbrevs=abbrevs, unknowns=unknowns, wait=wait, rec_depth=rec_depth+1)
                    l+= new_vals[0]
                    unknowns+= new_vals[1]

                if len(v.keys()) == 1:
                    vv = list(iter(v))[0].split(";")[0]

                    eq1 = Symbol(k)-Symbol(vv)
                    eq2 = Symbol("p_"+k)-Symbol("p_"+vv)

                    if str(k) in learning:
                        #print(str(k), "IN LEARNING")

                        eq1 -= Symbol(learning[k])
                        eq2 += Symbol(learning[k])

                    elif str(vv) in learning:
                        #print(str(vv), "IN LEARNING")

                        eq1 += Symbol(learning[vv])
                        eq2 -= Symbol(learning[vv])

                    #print("eq1",eq1)
                    #print("eq2",eq2)

                    l.append(eq1)
                    l.append(eq2)

        # generate elasticities
        if len(v.keys()) == 2:

            keys =  list(v.keys())

            k0 = keys[0].split(";")[0]
            k1 = keys[1].split(";")[0]
            Y1 = Symbol(k0)
            Y2 = Symbol(k1)

            p1 = Symbol("p_"+k0)
            p2 = Symbol("p_"+k1)

            k0 = k.split(";")[0].strip()
            k1 = k.split(";")[1].strip()
            sigma = "sigma_" + k0

            if k1 in production_dict:
                if "elast" in production_dict[k1]:
                    sigma = production_dict[k1]["elast"]

            elast = Symbol(sigma)

            s_eq = (Y1-Y2) - elast * (p2-p1)
            l.append(s_eq)
            print("   " * rec_depth, "    ", s_eq)

    else:
        pass

        # TODO think of a way to combine elasticities for more than two factors(?)


    unknowns = [str(u) for u in unknowns]

    print("   "*rec_depth,"< RETURN")
    return l, list(set(unknowns)), list(set(s)),list(set(abbrevs))


def make_list(x):
    if isinstance(x, list):
        return x
    else:
        return [x]


def apply_simplifications(expr,simplifications,wait="/",silent=False):

    out = []

    for e in make_list(expr):

        if not silent:
            wait = nextwait(wait)
            sys.stdout.write("  " + wait + "\r")

        e2 = e

        for i, simpl in enumerate(simplifications):

            s = simpl.split("=")
            s1 = Symbol(s[0].strip())

            ss1 = s[1].strip()

            if ss1 == "0":
                s2 = 0
            else:
                s2 = Symbol(str(ss1))

            if isinstance(e2,str):
                e2 = Symbol(e2)

            # if s[0].strip() == "p_V_X":
            #    print(str(s1),"->",str(s2),"                                    ")

            e2 = e2.subs(s1,s2,evaluate=True).simplify()

        # out.append(e2)
        if str(e2) != "0":
            out.append(e2)
            if not silent:
                sys.stdout.write( " %5s" %" " + str(e2)+"%50s\r\r"%" "+"\r")

        # print(" > ")

    # print("OUT",out)
    return list(set(out))


def gen_equation_system(t_prod, t_markets, production_dict, simplifications, learning):
    """
    :param t_prod: dict or list of dicts of production
    :param t_markets: dict or list of dicts of markets (sector aggregation)
    :param production_dict:
    :return:
    """

    equation_system = []
    unknown_system = []

    sys.stdout.write("Generating equation system...\n")

    # traverse

    unknowns = None
    lst = None
    s0 = None

    abbr = []

    for t in make_list(t_prod):

        lst,unknowns,s0,abbrevs = traverse(t, production_dict,learning)
        abbr += [a for a in abbrevs]

        # [print(l) for l in lst]  # print list of equations

        print("Juggling equations...")
        u = apply_simplifications(unknowns,simplifications)
        l = apply_simplifications(lst,simplifications)
        s = apply_simplifications(s0, simplifications)

        equation_system += l
        equation_system += s
        unknown_system += u

    for t in make_list(t_markets):

        lst,unknowns,s0,abbrevs = traverse(t, production_dict,learning)

        abbr += [a for a in abbrevs]

        print("Juggling equations...")
        u = apply_simplifications(unknowns,simplifications)
        l = apply_simplifications(lst,simplifications)
        s = apply_simplifications(s0, simplifications)

        equation_system += l
        equation_system += s
        unknown_system += u

    sys.stdout.write("done! %50s\n\n"%" ")

    # print("ABBREVS",abbr)

    return list(set(equation_system)), list(set(unknown_system)) + list(set(list(learning.values()))),list(set(abbr))



def convert_symbols(x):
    y = []

    for xi in x:
        if isinstance(xi,str):
            y.append(Symbol(xi))
        else:
            y.append(xi)

    return y

class CGEModel:

    def __init__(self, t_prod, t_markets, production_dict, simplifications,learning):
        """
        :param t_prod: dict or list of dicts of production
        :param t_markets: dict or list of dicts of markets (sector aggregation)
        :param production_dict:
        :param simplifications:

        e.g.

        # consumption sector
        t_prod = {
            "C": {
                "X;PFX": {
                    "V_X": {},
                    "S_X": {"E_X": {"V_E": {}}},
                },

            }
        }

        # value added sector
        t2= {
            "V;PFV": {
                "V_X": {},
                #"V_Y": {},
                "V_E": {}
            }
        }
        t_markets = [t2]

        # production parameters
        production_dict = {
            "PFC": {"type": "linear", "coeffs": ["theta_XC"]},
            "PFX": {"type": "linear", "coeffs": ["theta_XV", "theta_XS"]},

            "PFV": {"type": "linear", "coeffs": ["alpha_X", "alpha_E"]},
        }

        # simplifications
        simplifications = [
            "p_E_X = p_E",
            "p_V_X = p_V",
            "E_X = E",
            "p_V_E = p_V",
            "p_V = 0",
            "V = 0",
        ]

        # technological learning parameters
        learning = {
            "S_X": "A_X"
        }

        """

        eq_sys, unknowns, ident = gen_equation_system(t_prod, t_markets, production_dict, simplifications,learning)

        self.equations = eq_sys

        self.unknowns = convert_symbols(unknowns)   # + list(set(list(learning.values())))
        self.simplifications = simplifications
        self.parameter_identities = ident

    def __str__(self):
        return "<CGEMODEL[%i] with %i equations and %i unknowns>" % (id(self),len(self.equations),len(self.unknowns))

    def apply_simplifications(self,expr,silent=False):
        # expr: sympy expression or list of sympy expressions to simplify
        # :returns: simplified expr as list

        simple_expr = apply_simplifications(expr, self.simplifications,silent=silent)
        if len( simple_expr) == 1:
            return simple_expr[0]
        else:
            return simple_expr


    def printer(self):

         print("%i EQUATIONS\n"%(len(self.equations)))

         for k, i in enumerate(self.equations):
            #print("[%02i]" % k)
            sys.stdout.write("[%3i]  "%k)
            pprint(i,wrap_line =False)
            #print("\n")

         print("\n\n %i UNKNOWNS\n"%(len(self.unknowns)))

         for k, i in enumerate(self.unknowns):
                sys.stdout.write("[%3i]  " % k)
                #print("[%02i]" % k)
                pprint(i)

         print("\n\n %i IDENTITIES\n" % (len(self.parameter_identities)))

         for k, i in enumerate(self.parameter_identities):
             sys.stdout.write("[%3i]  " % k)
             # print("[%02i]" % k)
             pprint(i)

         print("\n")


    def filter_unknowns(self, equation_indices):

        equations = [self.equations[i] for i in equation_indices]

        u_selection = []

        for u in self.unknowns:

            for equation in equations:

                if isinstance(u,str):
                    u = Symbol(u)

                if u in equation.free_symbols:
                    u_selection.append(u)
                    break

        return u_selection



