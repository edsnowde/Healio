'use client'

import Hero from '@/components/KannadaHero'
import Link from 'next/link'

import {
ArrowRight,
Activity,
Brain,
BarChart3,
AlertTriangle
} from 'lucide-react'


export default function KannadaHome(){

return(

<main className="overflow-hidden">

<Hero/>


{/* Features */}
<section className="py-20 px-6 max-w-7xl mx-auto">

<h2 className="text-4xl font-bold text-center mb-16">
ಏಕೆ ಹೀಲಿಯೊ?
</h2>


<div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">


<div className="
bg-white
p-8
rounded-lg
shadow-card
hover:shadow-elevated
transition-shadow
">

<Activity className="w-12 h-12 text-primary mb-4"/>

<h3 className="text-xl font-bold mb-3">
ರೋಗಿ ನೋಂದಣಿ
</h3>

<p className="text-gray-600">
ಲಕ್ಷಣಗಳು ಮತ್ತು ಜೀವಚಿಹ್ನೆಗಳೊಂದಿಗೆ
ಡಿಜಿಟಲ್ ರೋಗಿ ನೋಂದಣಿ ವ್ಯವಸ್ಥೆ
</p>

</div>




<div className="
bg-white
p-8
rounded-lg
shadow-card
hover:shadow-elevated
transition-shadow
">

<Brain className="w-12 h-12 text-primary mb-4"/>

<h3 className="text-xl font-bold mb-3">
AI ತ್ರೈಯಾಜ್
</h3>

<p className="text-gray-600">
ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆ ಆಧಾರಿತ
ಅಪಾಯ ಮೌಲ್ಯಮಾಪನ ಮತ್ತು ಆದ್ಯತೆ ನಿರ್ಧಾರ
</p>

</div>




<div className="
bg-white
p-8
rounded-lg
shadow-card
hover:shadow-elevated
transition-shadow
">

<BarChart3 className="w-12 h-12 text-primary mb-4"/>

<h3 className="text-xl font-bold mb-3">
ವೈದ್ಯರ ಸರದಿ ವ್ಯವಸ್ಥೆ
</h3>

<p className="text-gray-600">
ರಿಯಲ್ ಟೈಮ್ ಆದ್ಯತೆ ಸರದಿ ಮತ್ತು
ಸಂಪನ್ಮೂಲ ಹಂಚಿಕೆ
</p>

</div>




<div className="
bg-white
p-8
rounded-lg
shadow-card
hover:shadow-elevated
transition-shadow
">

<AlertTriangle className="w-12 h-12 text-danger mb-4"/>

<h3 className="text-xl font-bold mb-3">
ರೋಗ ಸ್ಫೋಟ ಎಚ್ಚರಿಕೆ
</h3>

<p className="text-gray-600">
ರೋಗ ಗುಂಪು ಪತ್ತೆ ಮತ್ತು
ಸಾರ್ವಜನಿಕ ಆರೋಗ್ಯ ಮೇಲ್ವಿಚಾರಣೆ
</p>

</div>


</div>

</section>





{/* CTA */}
<section className="
py-20
px-6
bg-gradient-to-br
from-primary
to-primary/80
">

<div className="
max-w-4xl
mx-auto
text-center
text-white
">

<h2 className="text-4xl font-bold mb-6">
ರೋಗಿ ಆರೈಕೆಯನ್ನು ಪರಿವರ್ತಿಸಲು ಸಿದ್ಧವೇ?
</h2>

<p className="text-lg mb-8 text-green-50">
AI ಆಧಾರಿತ ತ್ರೈಯಾಜ್ ವ್ಯವಸ್ಥೆಯೊಂದಿಗೆ
ಕ್ಷಣಗಳಲ್ಲಿ ರೋಗಿ ನೋಂದಣಿ ಪ್ರಾರಂಭಿಸಿ
</p>



<div className="
flex flex-col
sm:flex-row
gap-4
justify-center
">

<Link
href="/kn/intake"
className="
inline-flex
items-center
justify-center
px-8 py-4
bg-white
text-primary
font-bold
rounded-lg
hover:bg-green-50
transition-colors
"
>
ಹೊಸ ರೋಗಿ ನೋಂದಣಿ

<ArrowRight className="ml-2 w-5 h-5"/>

</Link>



<Link
href="/kn/dashboard"
className="
inline-flex
items-center
justify-center
px-8 py-4
bg-green-700
text-white
font-bold
rounded-lg
hover:bg-green-800
transition-colors
border border-green-600
"
>

ವೈದ್ಯರ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್

<ArrowRight className="ml-2 w-5 h-5"/>

</Link>


</div>

</div>

</section>




{/* Footer */}
<footer className="
py-12
px-6
bg-gray-900
text-white
">

<div className="
max-w-7xl
mx-auto
text-center
">

<p className="text-gray-400">
© 2026 ಹೀಲಿಯೊ
ಪ್ರಾಥಮಿಕ ಆರೋಗ್ಯ ಕೇಂದ್ರಗಳಿಗಾಗಿ
AI ಆಧಾರಿತ ಆರೋಗ್ಯ ವ್ಯವಸ್ಥೆಗಳು
</p>

</div>

</footer>

</main>

)

}