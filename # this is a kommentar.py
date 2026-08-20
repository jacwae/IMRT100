# this is a kommentar 

print("hello world")
print(f"hello world number 2")

''' this is a long commentary'''


a = 6 #interger 
b = 1.2 #floatting point 
c = True # boolean
d = "test"#string
list1 = [1, 2, 3, 4]# list mutable 
f = (1, 2, 3, 4)# tuple immuntable 
print(f"the value of a is {a}\n")
print(" the value of is", c)
print('the value of lsit is, list1')

print(' the first letter of list is', list1[0])
print( 'the second item of list', list1[1])
print(' the last item of the list is',list1[-1])

list1[0]= 99
print(list1)
print('the tuple is',f)
f[0]=99
print(f[0])
list2 =[a,b, 4]
print (list1+list2)
list1.extend(list2)
print(list1)

value= input('type a value:')
print(' the result is', value)

v1= 3
v2= 4
print(f"the sum of v1 and v2 is, {v1+v2}")
print(f"the difference of v1 and v2 is, {v1-v2}")
print('v1*v2',v1*v2)
print('v1/v2',v1/v2)
print(v1**v2)


k = 5 
l= copy(k)
print(l)
l=3
print(k)

params = {'radius': 3, 'speed': 5, 'lenght': 6}
list = [3,5]
print(list)

print(list[0])

sensor = 5

var = sensor*params['lenght']
print(var)

# if statment
var =5 
threshold = 10
'''
if var >= threshold:
  print(' var is greater than or equal threshold')
  
if var < threshold:
  print ('var is smaller than threshold')
  '''
#elfi kan også bli brukt 
'''
list = [1, 2, 4, 55, 65, 20]

print(list[0:3])

# for loop
for i in list:
  if i >= threshold:
    print(f"the element {i} is greater than or eqaul")
  if i<threshold:
    print(f'the element {i} is smaller')


for i in range(4):
  print(f"the value of i is {i}")
'''

hemmelig_ord= input('skriv inn et hemmelig ord:')
user= input('gjett ordet:')

if user == hemmelig_ord:
    print ('du gjette riktig ord')
if user != hemmelig_ord:
        print('du gjettet feil ord, men du får et hint. det er noe gult')

