#!/usr/bin/env python
# coding: utf-8

# In[527]:


# import the needed packages
from nltk import CFG
from nltk.tree import Tree


# In[528]:


# A helper class to create node in the parsing tree
class Node:
    # Since the grammar may have only one term, so the right child is None by default
    def __init__(self, symbol, left, right=None):
        self.symbol = symbol
        self.left = left
        self.right = right
        self.parent = None

    def __repr__(self):
        return self.symbol

    def __str__(self):
        return self.symbol
    
    def set_parent(self, node):
        self.parent = node
    
    @classmethod
    def generate_tree(cls, node, cfg: CFG):
        # Get all original grammars
        grammar = str(cfg)
        grammar = grammar.split('\n')[1:]
        grammar = [x.strip(' ') for x in grammar]
        grammar = [x.replace("->", "").split() for x in grammar]
        
        # Case1
        if node.right is None:
            symbol = node.symbol
            
            parent = node.parent
            
            if(parent is None):
                if symbol in str(cfg):
                    return f"({symbol} {node.left})"
                else:
                    return f"{node.left}"
                
            if(node.right is None):
                if symbol in str(cfg):
                    return f"({symbol} {node.left})"
                else:
                    return f"{node.left}"
            
            # Can help distinguish VP-1s and VP-3s
            possible_symbols = []
            for rule in grammar:
                if(rule[0] == parent.symbol):
                    possible_symbols.extend(rule[1:])
            
            for rule in grammar:
                for s in possible_symbols:
                    if(rule[0] == s and rule[1] == node.left):
                        symbol = rule[0]
            
            return f"({symbol} {node.left})"
        
        # Case2
        if node.symbol not in str(cfg):
            left = Node.generate_tree(node.left, cfg)
            right = Node.generate_tree(node.right, cfg)
            symbol = node.symbol
            
            return f"{left} {right}"
        
        # Case3
        left = Node.generate_tree(node.left, cfg)
        right = Node.generate_tree(node.right, cfg)
        symbol = node.symbol
        
        return f"({symbol} {left} {right})"


# In[529]:


# Define a class as the CYK parser
class CYK:
    def __init__(self, grammar: CFG):
        self.cfg = grammar
        self.cnf = self.CFG_to_CNF(grammar)
        
    # A helper method for converting a CFG to CNF
    def get_all_related_rules(self, all_rules, to_replace):
        result = []
        for rule in all_rules:
            if(rule[0] == to_replace):
                result += [rule[1:]]
        return result
    
    def CFG_to_CNF(self, cfg: CFG):
        # convert CFG to a list
        # the string method of will automatically convert | to seperate rows
        grammar = str(cfg)
        grammar = grammar.split('\n')[1:]
        grammar = [x.strip(' ') for x in grammar]
        grammar = [x.replace("->", "").split() for x in grammar]

        # Need to handle the unit production
        unit_productions = []

        # Need to create a new rule, an index and a list to store the newly created rules
        index = 0

        # store the result rules
        result = []

        # store all rules, used for handling the unit production
        all_rules = []

        # Step1, if start symbol S appears on the RHS
        for rule in grammar:
            if("S" in rule[1:]):
                grammar.append(['SS', 'S'])
                break


        # Step2 Eliminate RHS with more than two non-terminal
        for rule in grammar:
            # to store the temporarily created new rules
            tmp_new_rules = []

            # case1: the simplest case: A -> X, don't consider A -> a, ie the unit productions
            if(len(rule) == 2 and rule[1][0] != "'"):
                unit_productions.append(rule)
                all_rules.append(rule)
                continue

            # case2: the more complex cases: A -> X Y or A -> X Y Z ... or A -> x Y or A -> X Y z
            if(len(rule) > 2):
                # Get the terminals in the current rule
                terminals = [[i, r] for i, r in enumerate(rule) if r[0] == "'"]

                # if there is any terminal, replace it with a new symbol and create a new rule
                if(len(terminals) > 0):
                    for pair in terminals:
                        rule[pair[0]] = rule[0] + str(index)
                        tmp_new_rules.append([rule[0] + str(index), pair[1]])
                        # Update the index
                        index += 1

                while(len(rule) > 3):
                    # Unceasingly parse the rule to just two terms, until there is only two non-temrinal terms
                    tmp_new_rules.append([rule[0] + str(index), rule[1], rule[2]])
                    rule = [rule[0]] + [rule[0] + str(index)] + rule[3:]
                    index += 1

            # Add the last remaining rules, modified rules with form A -> X Y, and terminal case A -> x
            result.append(rule)
            all_rules.append(rule)

            # Add the newly created rules to the result list
            if(len(tmp_new_rules) > 0):
                result += tmp_new_rules

        # Step3 handle the unit production A -> X or A -> Y or A -> etc.
        while(len(unit_productions) > 0):
            rule = unit_productions[0]
            unit_productions = unit_productions[1:]
            to_replace = self.get_all_related_rules(all_rules, rule[1])
            if(len(to_replace) > 0):
                for ele in to_replace:
                    new_rule = [rule[0]] + ele
                    if len(new_rule) > 2 or new_rule[1][0] == "'":
                        result.insert(0, new_rule)
                    else:
                        unit_productions.append(new_rule)
                    all_rules.append(new_rule)

        # only return the unique rules
        final = []
        for r in result:
            if r not in final:
                final.append(r)
        return final
    
    def parse(self, sentence : str):
        # Get the CNF of the given CFG
        cnf_grammar = self.cnf

        # Pre-process the given sentence
        sentence = sentence.split(' ')
        length = len(sentence)

        # Initialize the table
        table = [[[] for i in range(length)] for j in range(length)]
        # print(table)

        # Fill the diagonal line of the table as we discussed in class
        for i in range(length):
            for rule in cnf_grammar:
                if(len(rule) == 2):
                    if(("'" + sentence[i] + "'") == rule[1]):
                        table[i][i].append(Node(rule[0], ("'" + sentence[i] + "'")))
        # print(table)

        # Fill the remaining table
        for l in range(1, length):
            for i in range(length - l):
                j = i + l
                for k in range(i, j):
                    # Consider rule as A -> B C
                    for rule in cnf_grammar:
                        if(len(rule) != 3):
                            continue
                        # check if B in the cell [i][k]
                        # print(table[i][k])
                        node1 = []
                        for node in table[i][k]:
                            if(node.symbol == rule[1]):
                                node1.append(node)

                        # check if C in the cell [k+1][j]
                        node2 = []
                        for node in table[k + 1][j]:
                            if(node.symbol == rule[2]):
                                node2.append(node)

                        if(node1 != [] and node2 != []):
                            for node11 in node1:
                                for node22 in node2:
                                    if([rule[0], rule[1], rule[2]] in self.cnf):
                                        to_add = Node(rule[0], node11, node22)
                                        node11.set_parent(to_add)
                                        node22.set_parent(to_add)
                                        table[i][j].append(to_add)
        result = []
        # Only check if there is S in the right upper corner cell
        for node in table[0][length - 1]:
            if(node.symbol == "S"):
                result.append(node)
        
        # As required in the instruction, we need to return a list of nltk.tree.Tree objects
        final = []
        for node in result:
            final.append(Tree.fromstring(str(Node.generate_tree(node, self.cfg))))
        return final    


# In[530]:


# Test Cell, the example we discussed in class
cfg2 = CFG.fromstring("""
S -> NP VP
VP -> X1 PP
VP -> V NP
NP -> Det N
NP -> X2 PP
PP -> P NP
P -> 'in'
NP -> 'I' | 'elephant' | 'pyjamas'
N -> 'I' | 'elephant' | 'pyjamas'
V -> 'shot'
Det -> 'my' | 'the'
X1 -> V NP
X2 -> Det N
""")
parser2 = CYK(cfg2)
for tree in parser2.parse("I shot the elephant in my pyjamas"):
    tree.pretty_print()


# In[531]:


cfg3 = CFG.fromstring("""
S -> NP VP
VP -> V NP PP | V NP
NP -> N | Det N | Det N PP
PP -> 'in' NP
N -> 'I' | 'elephant' | 'pyjamas'
V -> 'shot'
Det -> 'my' | 'the'
""")
parser3 = CYK(cfg3)
for tree in parser3.parse("I shot the elephant in my pyjamas"):
    tree.pretty_print()


# In[532]:


f = open('french-grammar.txt', 'r')
test_cfg = CFG.fromstring(f.read())
test_parser = CYK(test_cfg)
test_parser.parse("je regarde la télévision")


# In[533]:


for tree in test_parser.parse("je regarde la télévision"):
    tree.pretty_print()


# In[534]:


for tree in test_parser.parse("le chat mange le poisson"):
    tree.pretty_print()


# In[535]:


for tree in test_parser.parse("tu regardes la télévision"):
    tree.pretty_print()


# In[536]:


for tree in test_parser.parse("il regarde la télévision"):
    tree.pretty_print()


# In[537]:


for tree in test_parser.parse("nous regardons la télévision"):
    tree.pretty_print()


# In[538]:


for tree in test_parser.parse("vous regardez la télévision"):
    tree.pretty_print()


# In[539]:


for tree in test_parser.parse("ils regardent la télévision"):
    tree.pretty_print()


# In[540]:


for tree in test_parser.parse("tu ne regardes pas la télévision"):
    tree.pretty_print()


# In[541]:


for tree in test_parser.parse("le chat ne mange pas le poisson"):
    tree.pretty_print()


# In[542]:


for tree in test_parser.parse("le chat"):
    tree.pretty_print()


# In[543]:


for tree in test_parser.parse("la télévision"):
    tree.pretty_print()


# In[544]:


for tree in test_parser.parse("les chats"):
    tree.pretty_print()


# In[545]:


for tree in test_parser.parse("les télévisions"):
    tree.pretty_print()


# In[546]:


for tree in test_parser.parse("Jonathan"):
    tree.pretty_print()


# In[547]:


for tree in test_parser.parse("Montréal"):
    tree.pretty_print()


# In[548]:


for tree in test_parser.parse("le Canada"):
    tree.pretty_print()


# In[549]:


for tree in test_parser.parse("il la regarde"):
    tree.pretty_print()


# In[550]:


for tree in test_parser.parse("le chat noir"):
    tree.pretty_print()


# In[551]:


for tree in test_parser.parse("le chat heureux"):
    tree.pretty_print()


# In[552]:


for tree in test_parser.parse("le beau chat"):
    tree.pretty_print()


# In[553]:


for tree in test_parser.parse("le joli chat"):
    tree.pretty_print()


# In[554]:


for tree in test_parser.parse("la dernière semaine"):
    tree.pretty_print()


# In[555]:


for tree in test_parser.parse("la semaine dernière"):
    tree.pretty_print()


# In[556]:


for tree in test_parser.parse("les chats noirs"):
    tree.pretty_print()


# In[557]:


for tree in test_parser.parse("la télévision noire"):
    tree.pretty_print()


# In[558]:


for tree in test_parser.parse("les télévisions noires"):
    tree.pretty_print()


# # Cannot be parse

# In[559]:


for tree in test_parser.parse("je mangent le poisson"):
    tree.pretty_print()


# In[560]:


for tree in test_parser.parse("les noirs chats mangent le poisson"):
    tree.pretty_print()


# In[561]:


for tree in test_parser.parse("la poisson mangent le poisson"):
    tree.pretty_print()


# In[562]:


for tree in test_parser.parse("je mange les"):
    tree.pretty_print()


# # Undergeneration

# In[563]:


for tree in test_parser.parse("Jonathan mange le poisson"):
    tree.pretty_print()


# # Overgeneration

# In[564]:


for tree in test_parser.parse("je mange le Jonathan"):
    tree.pretty_print()


# In[ ]:




