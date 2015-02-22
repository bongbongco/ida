# IDA plugin that converts all data in data segments to defined data types, and all data in code segments to code.
#
# Use by going to Options->Define data and code, or use the Alt+3 hotkey.
#
# Craig Heffner
# Tactical Network Solutions

import idc
import idaapi
import idautils

class Codatify(object):

    CODE = 2
    DATA = 3
    SEARCH_DEPTH = 25

    def __init__(self):
        pass

    # Get the start of the specified segment type (2 == code, 3 == data)
    def get_start_ea(self, attr):
        ea = idc.BADADDR
        seg = idc.FirstSeg()

        while seg != idc.BADADDR:
            if idc.GetSegmentAttr(seg, idc.SEGATTR_TYPE) == attr:
                ea = seg
                break
            else:
                seg = idc.NextSeg(seg)

        return ea

    # Creates ASCII strings
    def stringify(self):
        n = 0
        ea = self.get_start_ea(self.DATA)

        if ea == idc.BADADDR:
            ea = idc.FirstSeg()

        print ("Looking for possible strings starting at: %s:0x%X..." % (idc.SegName(ea), ea)),

        for s in idautils.Strings():
            if s.ea > ea:
                if not idc.isASCII(idc.GetFlags(s.ea)) and idc.MakeStr(s.ea, idc.BADADDR):
                    n += 1

        print "created %d new ASCII strings" % n

    # Converts remaining data into DWORDS.
    def datify(self):
        ea = self.get_start_ea(self.DATA)
        if ea == idc.BADADDR:
            ea = idc.FirstSeg()

        print "Converting remaining data to DWORDs...",

        while ea != idc.BADADDR:
            flags = idc.GetFlags(ea)

            if (idc.isUnknown(flags) or idc.isByte(flags)) and ((ea % 4) == 0):
                idc.MakeDword(ea)
                idc.OpOff(ea, 0, 0)

            ea = idc.NextAddr(ea)

        print "done."

    def pointify(self):
        counter = 0

        print "Renaming pointers...",

        for (name_ea, name) in idautils.Names():
            for xref in idautils.XrefsTo(name_ea):
                xref_name = idc.Name(xref.frm)
                if xref_name and xref_name.startswith("off_"):
                    i = 0
                    new_name = name + "_ptr"
                    while idc.LocByName(new_name) != idc.BADADDR:
                        new_name = name + "_ptr%d" % i
                        i += 1

                    if idc.MakeName(xref.frm, new_name):
                        counter += 1
                    #else:
                    #    print "Failed to create name '%s'!" % new_name

        print "renamed %d pointers" % counter

    # Creates functions and code blocks
    def codeify(self, ea=idc.BADADDR):
        func_count = 0
        code_count = 0

        if ea == idc.BADADDR:
            ea = self.get_start_ea(self.CODE)
            if ea == idc.BADADDR:
                ea = idc.FirstSeg()

        print "\nLooking for undefined code starting at: %s:0x%X" % (idc.SegName(ea), ea)

        if self.get_start_ea(self.DATA) == idc.BADADDR:
            print "WARNING: No data segments defined! I don't know where the code segment ends and the data segment begins."


        while ea != idc.BADADDR:
            try:
                if idc.GetSegmentAttr(ea, idc.SEGATTR_TYPE) == self.CODE:
                    if idc.GetFunctionName(ea) != '':
                        ea = idc.FindFuncEnd(ea)
                        continue
                    else:
                        if idc.MakeFunction(ea):
                            func_count += 1
                        elif idc.MakeCode(ea):
                            code_count += 1
            except:
                pass

            ea = idc.NextAddr(ea)

        print "Created %d new functions and %d new code blocks\n" % (func_count, code_count)



class codatify_t(idaapi.plugin_t):
    flags = 0
    comment = ""
    help = ""
    wanted_name = "Define all data and code"
    wanted_hotkey = ""

    def init(self):
        self.menu_context = idaapi.add_menu_item("Options/", "Fixup code", "Alt-3", 0, self.fix_code, (None,))
        self.menu_context = idaapi.add_menu_item("Options/", "Fixup data", "Alt-4", 0, self.fix_data, (None,))
        return idaapi.PLUGIN_KEEP

    def term(self):
        idaapi.del_menu_item(self.menu_context)
        return None

    def run(self, arg):
        pass

    def fix_code(self, arg):
        cd = Codatify()
        cd.codeify()

    def fix_data(self, arg):
        cd = Codatify()
        cd.stringify()
        cd.datify()
        cd.pointify()

def PLUGIN_ENTRY():
    return codatify_t()

