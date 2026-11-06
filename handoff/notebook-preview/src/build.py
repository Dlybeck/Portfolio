import os
D=os.path.dirname(os.path.abspath(__file__))
r=lambda n:open(os.path.join(D,n)).read()
L=r('index.r2.html').split('\n')
head='\n'.join(L[:275])            # title, fonts, base + round 1 css
r1js='\n'.join(L[458:728])         # LOGO, reduce, R1 (lines 459-728)
logo=r(os.path.join('..','logo.b64')).strip()
shell=r('shell.html').replace('LOGO_B64',logo)
out=head+'\n'+r('r2.css')+'\n'+r('r3.css')+'\n'+r('r4.css')+'\n'+r('r5.css')+'\n'+r('r6.css')+'\n'+r('r7.css')+'\n'+r('r8.css')+'\n'+r('r9.css')+'\n'+r('r11.css')+'\n'+r('r12.css')+'\n'+r('r13.css')+'\n'+r('r14.css')+'\n'+r('r15.css')+'\n'+r('r16.css')+'\n'+r('r17.css')+'\n'+r('r18.css')+'\n</style>\n\n'+shell+'\n<script>\n'+r1js+'\n'+r('r2.js')+'\n'+r('r3.js')+'\n'+r('r4.js')+'\n'+r('r5.js')+'\n'+r('r6.js')+'\n'+r('r9.js')+'\n'+r('r12.js')+'\n'+r('r13.js')+'\n'+r('r14.js')+'\n'+r('r15.js')+'\n'+r('r16.js')+'\n'+r('r17.js')+'\n'+r('r18.js')+'\n'+r('r7.js')+'\n'+r('r11.js')+'\n'+r('shell.js')+'\n</script>\n'
open(os.path.join(D,'index.html'),'w').write(out)
print(len(out))
