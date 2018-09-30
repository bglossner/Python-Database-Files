#!/usr/bin/python

l1 = []
l2 = []
with open("/home/pi/voltages.csv", "r") as f:
	l = f.readlines()
	print(l)
	#l2 = [x[6:] if "Ref1" in x else "" for x in l]
	for x in l:
		if "Ref1" in x:
			l1.append(((x[6:]).replace("\n", ",")).replace(" ", ""))
		else:
			l2.append((x[6:]).replace(" ", ""))
	
	#print("\n\n\n\n")
	#print(l1)
	#print("\n\n\n\n")
	#print(l2) 
	
with open("/home/pi/voltages2.csv", "w") as f:
	f.write("LS1_VA, LS1_VB, LS1_VC, LS2_VA, LS2_VB, LS2_VC\n")
	ll1 = len(l1)
	ll2 = len(l2)
	if ll1 >= ll2:
		for i in range(ll2):
			f.write("%s%s" % (l1[i], l2[i]))
		for i in range(ll1 - ll2):
			f.write("%s%s" % (l1[i], "0,0,0\n"))
	else:
		for i in range(ll1):
			f.write("%s%s" % (l1[i], l2[i]))
		for i in range(ll2 - ll1):
			f.write("%s%s" % ("0,0,0,", l2[i]))
