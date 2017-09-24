"""
VLSI CAD Design Tool - Boolean Expression to Transistor Netlist
Author: R.Mukesh, IIITDM Kancheepuram

Steps :
1. Read boolean expression
2. Convert expression to postfix
3. NOT (~) elimination from postfix
	|
	|--- Identify depth of NOT(~) effect in postfix
4. Postfix to TRANSISTOR NETLIST 
"""

print(
	"Welcome to RTL Compiler - Boolean Expression to Transistor Netlist\n"
	"Author : R. Mukesh (CED15I002)\n"
	"         IIITDM, Kancheepuram\n"
	)

print(
	"Format of Input Boolean Expression :\n"
	"~(~(A+B).C+~D)\n"
	"~(SUM1 + SUM2)\n"
	"\nSymbols : ~ (NOT), . (AND), + (OR)\n"
	)

__SYMBOLS__ = ['(',')','+','.','~',' ']

__OP_PRECEDENCE__ = {'~':3,'.':2,'+':1,'(':0,')':0}

# read boolean expression
print("Enter Boolean Expression")
expr_string = input().strip()

#Step 1 : EXTRACT INDIVIDIAL TOKENS FROM expr_string BY PARSING
tokens = []
substr_start = 0

for char_index in range(len(expr_string)):

	if expr_string[char_index] in __SYMBOLS__:
		
		if substr_start < char_index:
			tokens.append(expr_string[substr_start:char_index])

		if expr_string[char_index] != ' ':
			tokens.append(expr_string[char_index])

		substr_start = char_index+1

if substr_start < len(expr_string):
	tokens.append(expr_string[substr_start:len(expr_string)])


#Step 2 : CONVERT TOKENS TO POSTFIX NOTATION
operator_stack = []
tokens_postfix = []

for token_element in tokens:

	#classify as OPERATOR
	if token_element in __OP_PRECEDENCE__.keys():

		if token_element == '(':
			operator_stack.append(token_element)

		elif token_element == ')':
			while (operator_stack[-1] != '('):
				tokens_postfix.append(operator_stack.pop())

			#remove top-most '(' symbol
			operator_stack.pop()

		else:
			while (len(operator_stack)!=0) and (operator_stack[-1] != '(') and (__OP_PRECEDENCE__[operator_stack[-1]] >= __OP_PRECEDENCE__[token_element]):
				tokens_postfix.append(operator_stack.pop())

			operator_stack.append(token_element)

	#identify as INPUT VARIABLES
	else:
		tokens_postfix.append(token_element)

while len(operator_stack) !=0 :
	tokens_postfix.append(operator_stack.pop())

#Step 3 : NOT (~) ELIMINATION FROM POSTFIX
#	| --- For PMOS circuit
#	| --- For NMOS circuit	

tokens_postfix_pmos = tokens_postfix.copy()

#negate the nmos postfix expression
tokens_postfix_nmos = tokens_postfix.copy()
tokens_postfix_nmos.append('~')


# --- start of helper function - INVERT --- #

#NOTE : tokens_postfix original copy will be changed (Pass by Reference)
def invert(tokens_postfix, invert_index):

	#if token is a symbol
	if tokens_postfix[invert_index] not in __OP_PRECEDENCE__.keys():

		if tokens_postfix[invert_index][0] == '-':
			tokens_postfix[invert_index] = tokens_postfix[invert_index][1:]

		else:
			tokens_postfix[invert_index] = '-'+ tokens_postfix[invert_index]

		return invert_index;

	#if token is an OPERATOR (. or +)
	else:

		if tokens_postfix[invert_index] == '.':
			tokens_postfix[invert_index] = '+'

		elif tokens_postfix[invert_index] == '+':
			tokens_postfix[invert_index] = '.';

		chain_end = invert(tokens_postfix, invert_index-1)
		return invert(tokens_postfix, chain_end - 1)

# --- end of helper function - INVERT --- #


#Step 3 (i) : NOT (~) elimination in PMOS postix expr.
token_index = 0

while token_index < len(tokens_postfix_pmos):

	if tokens_postfix_pmos[token_index] == '~':
		invert(tokens_postfix_pmos, token_index - 1)
		tokens_postfix_pmos.pop(token_index)

	else:
		token_index += 1


#Step 3 (ii) : NOT (~) elimination in NMOS postfix expr.
token_index = 0

while token_index < len(tokens_postfix_nmos):

	if tokens_postfix_nmos[token_index] == '~':
		invert(tokens_postfix_nmos, token_index - 1)
		tokens_postfix_nmos.pop(token_index)

	else:
		token_index += 1

#Step 4 : Postfix to TRANSISTOR NETLIST
#	| --- Pull Down NMOS Network
#	| --- Pull up PMOS Network

#Step 4 (i) : generating NMOS (Pull Down) transistor netlist
postfix_eval_stack_nmos = []
nmos_index = 0
#index of last intersection/junction
nmos_jn_index = 0 

for token in tokens_postfix_nmos:

	if token not in ['.','+']:

		postfix_eval_stack_nmos.append([{ "name":("NMOS"+str(nmos_index)), "source":nmos_jn_index,"drain":nmos_jn_index+1, "gate":token}])
		#print(postfix_eval_stack_nmos)
		nmos_jn_index += 2
		nmos_index += 1

	elif token == '.':

		old_source = postfix_eval_stack_nmos[-1][0]["source"]
		new_source = postfix_eval_stack_nmos[-2][-1]["drain"]

		for transistor in postfix_eval_stack_nmos[-1]:
			if transistor["source"] == old_source:
				transistor["source"] = new_source

		postfix_eval_stack_nmos[-2].extend(postfix_eval_stack_nmos.pop(-1))
		
	elif token == '+':
		
		old_source = postfix_eval_stack_nmos[-1][0]["source"]
		new_source = postfix_eval_stack_nmos[-2][0]["source"]

		old_drain = postfix_eval_stack_nmos[-1][-1]["drain"]
		new_drain = postfix_eval_stack_nmos[-2][-1]["drain"]

		for transistor in postfix_eval_stack_nmos[-1]:

			if transistor["source"] == old_source:
				transistor["source"] = new_source

			if transistor["drain"] == old_drain:
				transistor["drain"] = new_drain

		postfix_eval_stack_nmos[-2].extend(postfix_eval_stack_nmos.pop(-1))


#Identify OUTPUT and GND pins
ground = postfix_eval_stack_nmos[0][0]["source"]
out_nmos = postfix_eval_stack_nmos[0][-1]["drain"]

for transistor in postfix_eval_stack_nmos[0]:

	if transistor["source"] == ground:
		transistor["source"] = "GND"

	if transistor["drain"] == out_nmos:
		transistor["drain"] = "OUTPUT"

#print(postfix_eval_stack_nmos)

#Step 4 (ii) : generating PMOS (Pull Up) transistor netlist

# --- start - helper function - invert input symbol --- #
def invert_input(token):

	if token[0] == '-':
		return token[1:]

	else:
		return "-"+token
# --- end - helper function - invert input symbol --- #


postfix_eval_stack_pmos = []
pmos_index = 0
#index of last intersection/junction
pmos_jn_index = nmos_jn_index 

for token in tokens_postfix_pmos:

	if token not in ['.','+']:

		postfix_eval_stack_pmos.append([{ "name":("PMOS"+str(pmos_index)), "source":pmos_jn_index,"drain":pmos_jn_index+1, "gate":invert_input(token)}])
		#print(postfix_eval_stack_pmos)
		pmos_jn_index += 2
		pmos_index += 1

	elif token == '.':

		old_source = postfix_eval_stack_pmos[-1][0]["source"]
		new_source = postfix_eval_stack_pmos[-2][-1]["drain"]

		for transistor in postfix_eval_stack_pmos[-1]:
			if transistor["source"] == old_source:
				transistor["source"] = new_source

		postfix_eval_stack_pmos[-2].extend(postfix_eval_stack_pmos.pop(-1))
		
	elif token == '+':
		
		old_source = postfix_eval_stack_pmos[-1][0]["source"]
		new_source = postfix_eval_stack_pmos[-2][0]["source"]

		old_drain = postfix_eval_stack_pmos[-1][-1]["drain"]
		new_drain = postfix_eval_stack_pmos[-2][-1]["drain"]

		for transistor in postfix_eval_stack_pmos[-1]:

			if transistor["source"] == old_source:
				transistor["source"] = new_source

			if transistor["drain"] == old_drain:
				transistor["drain"] = new_drain

		postfix_eval_stack_pmos[-2].extend(postfix_eval_stack_pmos.pop(-1))

#identify VDD and OUTPUT pins
vdd = postfix_eval_stack_pmos[0][0]["source"]
out_pmos = postfix_eval_stack_pmos[0][-1]["drain"]

for transistor in postfix_eval_stack_pmos[0]:

	if transistor["source"] == vdd:
		transistor["source"] = "VDD"

	if transistor["drain"] == out_pmos:
		transistor["drain"] = "OUTPUT"

#print(postfix_eval_stack_pmos)

input_symbols = set(tokens_postfix) - {'~','.','+'}
print("\nInputs: ",end='')
print(*input_symbols, sep = ', ')

print("No. of Transistors - PMOS : %d , NMOS : %d\n"%(pmos_index,nmos_index))

print("Transistor Netlist (NAME, SOURCE, DRAIN, GATE)\n")

print("PULL UP NETWORK (PMOS)\n")
for transistor in postfix_eval_stack_pmos[0]:
	print(transistor["name"], transistor["source"], transistor["drain"], transistor["gate"],sep='\t')

print("\nPULL DOWN NETWORK (NMOS)\n")
for transistor in postfix_eval_stack_nmos[0]:
	print(transistor["name"], transistor["source"], transistor["drain"], transistor["gate"],sep='\t')


# ======================================================================================================== #

print("\nPress any key to proceed to Simulation ...")
input()

"""
VLSI CAD Design Tool - Transistor Netlist Simulation
Author: R.Mukesh, IIITDM Kancheepuram

Steps :
1. Read input signal values
	|--- Generate complement of input signal values

2. Find all junctions/terminals short by simulating transistor behaviour
	]--- PMOS Transistor Netlist
	|--- NMOS Transistor Netlist

3. Find presence of path from Power/Ground to OUTPUT
	]--- PMOS Transistor Netlist
	|--- NMOS Transistor Netlist
"""

#Step 1: Read input signal values

#initialise all input signal values with 0
continue_simulation = True

while continue_simulation:

	input_signals_values = dict([(symbol,0) for symbol in input_symbols])

	#read input signal value and generate its complement
	print("\nEnter the value of INPUT SIGNALS\n")

	for signal in sorted(input_signals_values.keys()):
		print(signal,"= ",end='')
		input_signals_values[signal] = bool(int(input().strip()))
		input_signals_values["-"+signal] = not(input_signals_values[signal])


	#Step 2: Find all junctions/terminals short by simulating transistor behaviour
	pmos_netlist_short_jns = []
	nmos_netlist_short_jns = []

	#generating terminals/junctions short in PMOS netlist
	for transistor in postfix_eval_stack_pmos[0]:

		if input_signals_values[transistor["gate"]] == False:
			pmos_netlist_short_jns.append((transistor["source"],transistor["drain"]))

	#generating terminals/junctions short in NMOS netlists
	for transistor in postfix_eval_stack_nmos[0]:

		if input_signals_values[transistor["gate"]] == True:
			nmos_netlist_short_jns.append((transistor["source"],transistor["drain"]))

	#Step 3: Find presence of path from Power/Ground to OUTPUT

	# Find path from GND to OUTPUT in NMOS netlist
	initial_gnd_short = ["GND"]
	transistive_gnd_short = []

	nmos_output = "Z"

	#until 'initial gnd_short' is not empty, i.e., NO MORE PATH FORWARD
	while len(initial_gnd_short) != 0:

		transistive_gnd_short = []

		#generating the next hops using present hops
		for source_terminal, drain_terminal in nmos_netlist_short_jns:
			if source_terminal in initial_gnd_short:
				transistive_gnd_short.append(drain_terminal)

		#path found from GROUND to OUTPUT
		if "OUTPUT" in transistive_gnd_short:
			nmos_output = 0
			break

		initial_gnd_short = transistive_gnd_short


	# Find path from POWER(vdd) to OUTPUT in PMOS netlist
	initial_vdd_short = ["VDD"]
	transistive_vdd_short = []

	pmos_output = "Z"

	#until 'initial vdd_short' is not empty, i.e., NO MORE PATH FORWARD
	while len(initial_vdd_short) != 0:

		transistive_vdd_short = []

		#generating the next hops using present hops
		for source_terminal, drain_terminal in pmos_netlist_short_jns:
			if source_terminal in initial_vdd_short:
				transistive_vdd_short.append(drain_terminal)

		#path found from VDD to OUTPUT
		if "OUTPUT" in transistive_vdd_short:
			pmos_output = 1
			break

		initial_vdd_short = transistive_vdd_short

	print("\nPMOS OUTPUT :",pmos_output)
	print("NMOS OUTPUT :",nmos_output)

	print("\nDo you want to continue simulation (Y/N) : ",end='')
	continue_simulation = True if (input().strip() == "Y") else False