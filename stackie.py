import math
import noise
import random
import operator
import collections
from PIL import Image

ops = {
    'r': (0, lambda: 'random.random()'),
    'P': (0, lambda: 'math.pi'),
    'd': (1, lambda x: (x, x)),
    ':': (2, lambda x, y: (y, x)),
    ';': (3, lambda x, y, z: (z, y, x)),
    's': (1, lambda x: f'math.sin({x})'),
    'c': (1, lambda x: f'math.cos({x})'),
    'q': (1, lambda x: f'math.sqrt({x})'),
    'l': (1, lambda x: f'math.log({x})'),
    '~': (1, lambda x: f'abs({x})'),
    '!': (1, lambda x: f'1 - {x}'),
    '#': (1, lambda x: f'round({x})'),
    '$': (1, lambda x: f'math.floor({x})'),
    #'e': None, # TODO
    '?': (1, lambda x: f'1 if ({x}) > 0 else 0'),
    'p': (2, lambda x, y: f'noise.pnoise2({x}, {y})*0.5+0.5'),
    'a': (2, lambda x, y: f'math.atan2({x}, {y})'),
    '+': (2, lambda x, y: f'({x})+({y})'),
    '-': (2, lambda x, y: f'({x})-({y})'),
    '*': (2, lambda x, y: f'({x})*({y})'),
    '/': (2, lambda x, y: f'({x})/({y})'),
    '^': (2, lambda x, y: f'({x})**({y})'),
    '>': (2, lambda x, y: f'max({x})'),
    '<': (2, lambda x, y: f'min({x})'),
    #'E': None, # TODO
    #'w': None, # TODO
    #'W': None # TODO
}

def comp(s):
    stack = collections.deque()

    for c in s:
        if c in 'xy0123456789':
            stack.append(c)
        elif c in 'd:;':
            args = reversed([stack.pop() for _ in range(ops[c][0])])
            stack.extend(ops[c][1](*args))
        else:
            if c not in ops or len(stack) < ops[c][0]:
                raise RuntimeError
            args = reversed([stack.pop() for _ in range(ops[c][0])])
            #ret = ops[c][1](*args)
            stack.append(ops[c][1](*args))

    compiled = compile(stack[-1], '', 'eval')
    return lambda x, y: eval(compiled, globals(), {'x': x, 'y': y})

def gen_image(s):
    fn = comp(s)

    img = Image.new('L', (256, 256))
    img.putdata([int(255*fn(x/255, y/255)) for y in range(256) for x in range(256)])

    return img

if __name__ == '__main__':
    gen_image(input()).show()
