"""
What we need to do :

Additional software requirements 

At the beginning of the game, the human player indicates the length of the string of numbers to be used in the game,
which may be in the range of 15 to 25 numbers. The game software randomly generates a string of numbers according to the 
specified length, including numbers from 1 to 6. 

Game description 

At the beginning of the game, the generated string of numbers is given. Players take turns. 
The total number of points is 0 (points are not counted for each player individually).
A game bank is used and initially it is equal to 0. During a turn, a player may:  

add a pair of numbers (first with second, third with fourth, fifth with sixth, etc.) and write the sum in the
place of the pair of numbers added 
(if the sum is greater than 6, substitutions are made: 7 = 1, 8 = 2, 9 = 3, 10 = 4, 11 = 5, 12 = 6),
and add 1 point to the total score, or  

delete a number left unpaired and subtract one point from the total score.  

The game ends when one number remains in the number string. At the end of the game, the bank is 
added to the total number of points. If both the number left in the number string and the total number of points
are even numbers, the player who started the game wins. If both the number in the number string and the total 
number of points is an odd number, the second player wins. In all other cases, the result is a draw. 
"""

import random

def set_up():
    length = int(input("Enter the length of the string (15-25): "))
    while length < 15 or length > 25:
        print("Please enter a number between 15 and 25.")
        length = int(input("Enter the length of the string (15-25): "))

    numbers = [random.randint(1, 6) for _ in range(length)]
    return numbers



def main():
    numbers = set_up()
    print("Generated numbers:", numbers)


main()
