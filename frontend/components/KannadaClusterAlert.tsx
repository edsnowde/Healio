import { Bell } from 'lucide-react'


interface ClusterAlertProps{
message:string
}

export default function KannadaClusterAlert({
message
}:ClusterAlertProps){

return(

<div className="
bg-danger/10
border border-danger
rounded-lg
p-4
flex items-start gap-3
">

<div className="
flex-shrink-0 mt-0.5
">

<Bell className="
w-5 h-5 text-danger
animate-pulse
"/>

</div>


<div className="flex-1">

<h3 className="
font-bold text-danger mb-1
">
ರೋಗ ಸ್ಫೋಟ ಮೇಲ್ವಿಚಾರಣೆ ಎಚ್ಚರಿಕೆ
</h3>

<p className="
text-gray-700 text-sm
">
{message}
</p>

</div>


<button className="
text-sm
text-danger
font-medium
">
ಪರಿಶೀಲಿಸಿ
</button>

</div>

)

}