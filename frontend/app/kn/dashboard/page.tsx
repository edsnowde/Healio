'use client'

import { useState,useEffect } from 'react'
import QueueBoard from '@/components/KannadaQueueBoard'
import ClusterAlert from '@/components/KannadaClusterAlert'
import { TrendingUp } from 'lucide-react'


interface Patient{
id:string
name:string
age:number
priority:'red'|'yellow'|'green'
riskScore:number
symptoms:string
assignedDoctor:string
intakeTime:string
estimatedWait:number
}


export default function KannadaDashboardPage(){

const [patients,setPatients]=useState<Patient[]>([])
const [alerts,setAlerts]=useState<string[]>([])



useEffect(()=>{

const mockPatients:Patient[]=[

{
id:'PAT-2626-0451',
name:'Rajesh Kumar',
age:45,
priority:'red',
riskScore:89,
symptoms:'ತೀವ್ರ ಎದೆ ನೋವು, ಉಸಿರಾಟ ತೊಂದರೆ',
assignedDoctor:'ಡಾ. ರಾಹುಲ್ ವರ್ಮಾ',
intakeTime:'09:15',
estimatedWait:2
},

{
id:'PAT-2626-0450',
name:'Priya Sharma',
age:32,
priority:'yellow',
riskScore:72,
symptoms:'ಮಧ್ಯಮ ಜ್ವರ, ಕೆಮ್ಮು',
assignedDoctor:'ಡಾ. ಪ್ರಿಯಾ ಶರ್ಮಾ',
intakeTime:'09:22',
estimatedWait:8
},

{
id:'PAT-2626-0449',
name:'Amit Patel',
age:28,
priority:'yellow',
riskScore:65,
symptoms:'ತಲೆನೋವು, ದೇಹನೋವು',
assignedDoctor:'ಡಾ. ಮೀರಾ ಗುಪ್ತಾ',
intakeTime:'09:30',
estimatedWait:15
},

{
id:'PAT-2626-0448',
name:'Neha Singh',
age:55,
priority:'green',
riskScore:42,
symptoms:'ಸಾಮಾನ್ಯ congestion',
assignedDoctor:'ಡಾ. ರಾಹುಲ್ ವರ್ಮಾ',
intakeTime:'09:35',
estimatedWait:22
},

{
id:'PAT-2626-0447',
name:'Vikram Desai',
age:38,
priority:'green',
riskScore:38,
symptoms:'ಸಾಮಾನ್ಯ ಪರಿಶೀಲನೆ',
assignedDoctor:'ಡಾ. ಪ್ರಿಯಾ ಶರ್ಮಾ',
intakeTime:'09:42',
estimatedWait:30
}

]


setPatients(mockPatients)


setAlerts([
'ವಾರ್ಡ್-3: 5 ಉಸಿರಾಟ ಲಕ್ಷಣ ಗುಂಪು ಪತ್ತೆ',
'ಡಾ. ರಾಹುಲ್ ವರ್ಮಾ: 3 ತುರ್ತು ರೋಗಿಗಳು ಸರದಿಯಲ್ಲಿ'
])


},[])




const stats={
totalPatients:patients.length,

urgentCount:
patients.filter(
p=>p.priority==='red'
).length,

moderateCount:
patients.filter(
p=>p.priority==='yellow'
).length
}



return(

<main className="
min-h-screen
py-12 px-6
bg-gradient-to-br
from-slate-50
to-slate-100
">

<div className="
max-w-7xl
mx-auto
">


{/* Header */}
<div className="mb-8">

<h1 className="
text-4xl font-bold
text-gray-900 mb-2
">
ವೈದ್ಯರ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್
</h1>

<p className="text-gray-600">
ರಿಯಲ್ ಟೈಮ್ ರೋಗಿ ಸರದಿ ಮತ್ತು ವೈದ್ಯಕೀಯ ಬುದ್ಧಿಮತ್ತೆ
</p>

</div>




{/* Alerts */}
{
alerts.length>0 &&(

<div className="
mb-8
space-y-4
">

{
alerts.map(
(alert,idx)=>(
<ClusterAlert
key={idx}
message={alert}
/>
))
}

</div>

)
}




{/* Stats */}
<div className="
grid md:grid-cols-3
gap-6 mb-8
">


<div className="
bg-white
rounded-lg
shadow-card
p-6
border-l-4 border-primary
">

<p className="
text-gray-600
text-sm font-medium
">
ಒಟ್ಟು ರೋಗಿಗಳು
</p>

<p className="
text-3xl font-bold
text-gray-900
">
{stats.totalPatients}
</p>

<p className="
text-xs text-gray-500 mt-2
">
ಇಂದಿನ ಸಕ್ರಿಯ ಸರದಿ
</p>

</div>





<div className="
bg-white
rounded-lg
shadow-card
p-6
border-l-4 border-priority-red
">

<p className="
text-gray-600
text-sm font-medium
">
ತುರ್ತು (ಕೆಂಪು)
</p>

<p className="
text-3xl font-bold
text-priority-red
">
{stats.urgentCount}
</p>

<p className="
text-xs text-gray-500 mt-2
">
ತಕ್ಷಣ ಚಿಕಿತ್ಸೆ ಅಗತ್ಯ
</p>

</div>





<div className="
bg-white
rounded-lg
shadow-card
p-6
border-l-4 border-priority-yellow
">

<p className="
text-gray-600
text-sm font-medium
">
ಮಧ್ಯಮ (ಹಳದಿ)
</p>

<p className="
text-3xl font-bold
text-priority-yellow
">
{stats.moderateCount}
</p>

<p className="
text-xs text-gray-500 mt-2
">
ಫಾಲೋಅಪ್ ಅಗತ್ಯ
</p>

</div>


</div>




{/* QueueBoard same component for now */}
<QueueBoard
patients={patients}
/>





{/* Footer Insights */}
<div className="
mt-8
bg-white
rounded-lg
shadow-card
p-6
">

<div className="
flex gap-4 items-start
">

<TrendingUp className="
w-5 h-5
text-primary
flex-shrink-0 mt-1
"/>

<div>

<h3 className="
font-bold text-gray-900 mb-2
">
ಸರದಿ ವಿಶ್ಲೇಷಣೆ
</h3>

<p className="
text-gray-600 text-sm
">

ಸರಾಸರಿ ಕಾಯುವ ಸಮಯ:
<strong>
12 ನಿಮಿಷ
</strong>

{" | "}

ವ್ಯವಸ್ಥೆ ದಕ್ಷತೆ:
<strong>
94%
</strong>

{" | "}

ಮುಂದಿನ ಲಭ್ಯ ವೈದ್ಯರು:
<strong>
ಡಾ. ಮೀರಾ ಗುಪ್ತಾ (3 ನಿಮಿಷ)
</strong>

</p>

</div>

</div>

</div>



</div>

</main>

)

}