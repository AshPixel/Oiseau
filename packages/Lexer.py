from re import match
from packages.ErrorManager import SimpleError

class Lexer:
    def __init__(self, file) -> None:
        self.file  = file
        self.tokens = []
        
        self.tokenize()
    
    def tokenize(self):
        tickets = self.ticketize(self.file.replace(' ', 'α').replace('\n', 'β').replace('\\\"', "γ").replace('\\\\', "δ").replace('\\t', "ε").replace('\\n', 'ζ'))
        
        for ticket in tickets:
            if match(r"\%.*?\%", ticket) or ticket in ['\n']: continue
            elif match(r"(fun|if|elif|else|while|switch|case|clear|delay|execute|write)\b", ticket): self.addToken("COMMAND", ticket)
            elif match(r"(true|false)\b", ticket): self.addToken("BOOLEAN", ticket)
            elif match(r"(\-)?[0-9_]+\.[0-9_]+", ticket): self.addToken("DECIMAL", ticket.replace('_', ''))
            elif match(r"(empty)\b", ticket): self.addToken("EMPTY", 'empty')
            elif match(r"(\-)?([0-9_]+|infinity)", ticket): self.addToken("INTEGER", ticket.replace('_', ''))
            elif match(r"<(.*?)>", ticket): 
                args = [ticket[:-1].rsplit('<', 1)[1].replace(',', '')]
                self.addToken("STORAGE", Lexer('' if args == [''] else ','.join(args)).tokens)
            elif match(r"\"(.*?)\"", ticket): self.addToken("STRING", ticket)
            elif match(r"(\!)?(boolean|decimal|integer|string)\b", ticket): self.addToken("DATATYPE", ticket if ticket != "mty" else "empty")
            elif match(r"[A-Za-z]+[A-Za-z0-9]*(\((.*?)\))", ticket):
                args = [ticket[:-1].rsplit('(', 1)[1].replace(',', '')]
                self.addToken("CALL", ticket[:-1].rsplit('(', 1)[0], Lexer('' if args == [''] else ','.join(args)).tokens)
            elif match(r"\((.*?)\)", ticket):
                args = [ticket[:-1].rsplit('(', 1)[1].replace(',', '')]
                self.addToken("ARGUMENT", Lexer('' if args == [''] else ','.join(args)).tokens)
            elif match(r"(\!)?[A-Za-z]+[A-Za-z0-9\-\_]*", ticket): self.addToken("IDENTIFIER", ticket)
            elif ticket.replace('~', '=') in ['=', '+=', '-=', '/=', '*=', '^=', '#=']: self.addToken("ASSIGN", ticket.replace('~', '='))
            elif ticket.replace('~', '=') in ['==', '!=', '>=', '<=', '>', '<']: self.addToken("COMPARATOR", ticket.replace('~', '='))
            elif ticket in ['+', '-', '*', '/']: self.addToken("OPERATOR", ticket)
            elif ticket in ["++", "--"]: self.addToken("SHORT_MOD", ticket)
            elif ticket == "{": self.addToken("OPEN_CURLY_BRACKET", ticket)
            elif ticket == "}": self.addToken("CLOSE_CURLY_BRACKET", ticket)
            elif ticket == ':': self.addToken("COLON", ticket)
            elif ticket == ';': self.addToken("STATEMENT_END", ticket)
            elif ticket != ' ': SimpleError("UnknownCharacterError", f"{ticket} was a unknown character")
    
    def ticketize(self, file):
        tStr = []
        isolate = ['%', '"', ':', ';', "~", "=", "(", ",", ")", "{", "}", "<", ">", "+", "*", "!", "-", "/", "α", "β", "γ", "δ", "ε", "ζ"]
        capture = ['%', '"', "(", ")", "<", ">"]
        capturing = False
        for idx, data in enumerate(file):            
            d = data.replace("α", ' ').replace("β", '\n').replace("γ", "\\\"").replace("δ", "\\\\").replace("ε", '\\t').replace("ζ", '\\n')
            
            if file[idx - 1] in isolate or data in isolate:
                if data in capture: capturing = not capturing
                tStr.append(d)
                continue
            if tStr != []: tStr[-1] += d
            else: tStr.append(d)
        
        holdType = ""
        tickets = []
        holding  = []
        
        for idx, data in enumerate(tStr):
            if data == "%":
                if holdType == "": holdType = "COMMENT"
                elif holdType in ["STRING"]: holding.append(data)
                elif holdType == "COMMENT":
                    tickets.append(f"%{''.join(holding)}%")
                    holdType = ""
                    holding = []
                else: SimpleError("NotStartedError", "the comment wasn't started.")
            elif data == "\"":
                if holdType == "": holdType = "STRING"
                elif holdType in ["COMMENT", "ARGUMENT", "STORAGE"]: holding.append(data)
                elif holdType == "STRING":
                    tickets.append(f"\"{''.join(holding)}\"")
                    holdType = ""
                    holding = []
                else: SimpleError("NotStartedError", "the string wasn't started.")
            elif data == "(":
                if holdType == "": holdType = "ARGUMENT"
                elif holdType in ["COMMENT", "STRING"]: holding.append(data)
                else: SimpleError("UnexpectedStartError", "the argument was randomly started.")
            elif data == ")":
                if holdType in ["COMMENT", "STRING"]: holding.append(data)
                elif holdType == "ARGUMENT":
                    if match("[A-Za-z]+[A-Za-z0-9\-\_]*", tickets[-1]): tickets[-1] += f"({''.join(holding)})"
                    else: tickets.append(f"({''.join(holding)})")
                    
                    holdType = ""
                    holding = []
                else: SimpleError("NotStartedError", "the argument wasn't started.")
            elif data == "<":
                if holdType == "": holdType = "STORAGE"
                elif holdType in ["COMMENT", "STRING"]: holding.append(data)
                else: SimpleError("UnexpectedStartError", "the storage type was randomly started.")
            elif data == ">":
                if holdType in ["COMMENT", "STRING"]: holding.append(data)
                elif holdType == "STORAGE":
                    tickets.append(f"<{''.join(holding)}>")
                    
                    holdType = ""
                    holding = []
                else: SimpleError("NotStartedError", "the storage type wasn't started.")
            elif data in ["~", "="] and tickets[-1] in ["~", "=", "!", "?", ">", "<", "+", "-", "/", "*", '^', '#']: tickets[-1] += data
            elif data in ["+", "-"] and tickets[-1] == data: tickets[-1] += data
            elif tickets != [] and tickets[-1] == "!":
                if holdType == "": tickets[-1] += data
                else: holding[-1] += data
            else:
                if holdType == "": tickets.append(data)
                else: holding.append(data)
        return tickets
    
    def addToken(self, type_, content, args = None):
        self.tokens.append({"type": type_, "content": content})
        
        if args != None: self.tokens[-1].update({"args": args})