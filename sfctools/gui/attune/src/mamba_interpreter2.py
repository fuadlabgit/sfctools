"""
Mamba interpreter ver 0.2
"""

import re



def process_line(line,r=0):
    # recursion dpeth


    # transaction definitions
    for match in re.finditer(r'\<\~\~\>\s+[\(\)A-Za-z0-9,\@\s\_]+',line):
        start, end = match.span()
        mstr = match.group(0)


        try:

            line = line.replace("<~~>", '').replace(" ", '')

        except:
            pass


    # replace agent references
    for match in re.finditer(r'\@[A-Za-z0-9_]+',line):
        start, end = match.span()
        mstr = match.group(0)
        line = line.replace(mstr,"self.%s" % mstr[1:]) # .lower()

    # power
    line = line.replace("^", "**")

    # time reference
    line = line.replace("$.TIME", "Clock().get_time()")

    # end
    line = line.replace("$[END]","\n")

    # self.
    line = line.replace("$.", "self.")

    # random number
    line = line.replace("$URAND", "np.random.rand()")


    # balance sheet stuff
    code = {
    "BALANCE?" : "self.balance_sheet.get_balance",
    "INCOME?": "self.income_statement.get_entry",
    "ASSETS": "BalanceEntry.ASSETS",
    "EQUITY": "BalanceEntry.EQUITY",
    "LIABILITIES": "BalanceEntry.LIABILITIES",
    "REVENUES": "ICSEntry.REVENUES",
    "GAINS":"ICSEntry.GAINS",
    "EXPENSES": "ICSEntry.EXPENSES",
    "LOSSES": "ICSEntry.LOSSES",
    "NONTAX_PROFITS": "ICSEntry.NONTAX_PROFITS",
    "INTEREST": "ICSEntry.INTEREST",
    "TAXES": "ICSEntry.TAXES",
    "NOI": "ICSEntry.NOI"
    }
    for k,v in code.items():
        line = line.replace(k,v)

    return (2+r)*"\t" + line + "\n"



def convert_code(codelines):

    mydict = {} # maps lines to code
    mycode_idx = 0

    import_code = """
from sfctools import World, Agent, Clock, Settings, BalanceEntry, ICSEntry
import numpy as np

from .transactions import *
"""

    knows_code = """
\t\tdef link(self):\n
"""

    mycode = ""

    r = 0 # recursion depth for nested statements

    line_idx = 0
    for line in codelines:

        if line.startswith("$[AGENT]"):  # agent definition starts

            try:
                mydef = line.split("$[AGENT]")[1].strip()
                #name = mydef[0].capitalize() + mydef[1:].split(".")[0]
                name = mydef[0] + mydef[1:].split(".")[0]

                my_args = mydef[1:].split(" ")

                cls_name = "Agent"

                if len(my_args) > 1:
                    cls_name = my_args[1]
                    cls_name = cls_name.replace("(","").replace(")","")
                    #name = mydef[0].capitalize() + my_args[0]
                    name = mydef[0] + my_args[0]

                mycode += """
class %s(%s):

\t\tdef __init__(self):
\t\t\tsuper().__init__()
""" % (name,cls_name)
            except:

                return "ERROR please specify name after $[AGENT]",mydict
        elif line.startswith("$[CLASS]"):  # agent definition starts

            try:
                mydef = line.split("$[CLASS]")[1].strip()
                #name = mydef[0].capitalize() + mydef[1:].split(".")[0]
                name = mydef[0] + mydef[1:].split(".")[0]

                my_args = mydef[1:].split(" ")

                cls_name = ""

                if len(my_args) > 1:
                    cls_name = my_args[1]
                    cls_name = cls_name.replace("(","").replace(")","")
                    #name = mydef[0].capitalize() + my_args[0]
                    name = mydef[0] + my_args[0]

                mycode += """
class %s(%s):

\t\tdef __init__(self):
\t\t\tsuper().__init__()
""" % (name,cls_name)
            except:

                return "ERROR please specify name after $[AGENT]",mydict

        elif line.startswith("$[MARKET]"):  # market definition starts

            try:
                mydef = line.split("$[MARKET]")[1].strip()
                #name = mydef[0].capitalize() + mydef[1:].split(".")[0]
                name = mydef[0] + mydef[1:].split(".")[0]

                my_args = mydef[1:].split(" ")

                cls_name = "MarketMatching"
                import_code += "from sfctools import MarketMatching\n"

                mycode += """
class %s(%s):

\t\tdef __init__(self):
\t\t\tsuper().__init__()
""" % (name,cls_name)
            except:

                return "ERROR please specify name after $[AGENT]",mydict


        elif line.startswith("+[PARAM]"):

            try:
                params = line.split("+[PARAM]")[1].strip()
                params = [p.strip() for p in params.split(",")]

                for p in params:
                    mycode += "\t\t\tself.%s = Settings().get_hyperparameter('%s')\n" % (p,p)
                mycode += "\n"

            except:
                pass

        elif line.startswith("+[KNOWS]"):

            try:
                knowns = line.split("+[KNOWS]")[1].strip()
                knowns = [k.strip() for k in knowns.split(",")]

                for k in knowns:
                    mycode += "\t\t\tself.%s = None\n" % (k)
                    # knows_code += "\t\t\tself.%s = World().get_agents_of_type('%s')\n" % (k.lower(),k.capitalize())
                    knows_code += "\t\t\tself.%s = World().get_agents_of_type('%s')\n" % (k,k)

                mycode += "\n" + knows_code + "\n"

            except:
                pass

        elif line.startswith("+[IMPORT]"):

            try:
                statement = line.split("+[IMPORT]")[1].strip()
                import_code += statement + "\n"

            except:
                pass

        elif line.startswith("+[IMPORT]"):

            try:
                statement = line.split("+[IMPORT]")[1].strip()
                import_code += statement + "\n"

            except:
                pass

        elif line.startswith("+[ENDFUN]") or line.strip().startswith("+[ENDACCOUNTING]"):
            r -= 1

        elif line.startswith("+[FUN]"):
            r += 1

            try:
                mydef = line.split("+[FUN]")[1]

                my_args = mydef.split(" ")
                fun_name = my_args[1]

                if len(my_args) > 2:

                    my_params = [s.replace("(","").replace(")","").strip() for s in my_args[2].split(",")]
                    mycode += "\t\tdef %s(self,%s):\n" % (fun_name, ",".join(my_params))

                else:

                    mycode += "\t\tdef %s(self):\n" % (fun_name)


            except:
                pass

        elif line.strip().startswith("+[ACCOUNTING]"):
            r += 1

            try:

                # beginning of
                mycode += "\t" + "\t"*(r+line.count("\t")) + "with self.balance_sheet.modify:\n"

            except:
                pass

        elif line.strip().startswith("<>"):

            try:
                s = line.split("<>")[1].strip()
                mycode += process_line("\t"*(r+line.count("\t")) +"self.balance_sheet.change_item(%s)"  % s)

            except:
                pass

        elif line.strip().startswith("<.>"):

            try:
                s = line.split("<.>")[1].strip()
                mycode += process_line("\t"*(r+line.count("\t")) +"self.balance_sheet.change_item(%s,suppress_stock=True)"  % s)

            except:
                pass

        elif line.startswith("+[INIT]"):
            r += 1

        elif line.startswith("+[ENDINIT]"):
            r -= 1


        else:
            mycode += process_line(line,r)


        mycode_idx = len(import_code.split("\n")) + len(mycode.split("\n"))
        mydict[line_idx] = mycode_idx
        line_idx += 1


        if line.startswith("$[END]"):
            all_code = import_code + "\n" + mycode
            all_code = all_code.encode('utf-8') # replace non utf-8
            all_code = str(all_code.decode("utf-8", "replace"))

            return all_code,mydict

    return "ERROR missing $[END]",mydict
