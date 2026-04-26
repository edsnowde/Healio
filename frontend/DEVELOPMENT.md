# Frontend Development Guide

## Architecture

```
components/
├── Layout Components
│   ├── Navbar.tsx          - Navigation header
│
├── Page Components  
│   ├── Hero.tsx            - Landing hero section
│   ├── PatientForm.tsx     - Intake form
│   ├── TriageCard.tsx      - Results display
│   ├── QueueBoard.tsx      - Queue management
│
├── Utility Components
│   ├── VoiceInput.tsx      - Voice capture UI
│   ├── SymptomUpload.tsx   - Image upload UI
│   └── ClusterAlert.tsx    - Alert banner
```

## Styling

- **Tailwind CSS**: Utility-first styling
- **Custom Classes**: `/app/globals.css`
- **Color Scheme**:
  - Primary: Green (#059669)
  - Secondary: Orange (#f97316)
  - Red (Urgent): #dc2626
  - Yellow (Moderate): #f59e0b
  - Green (Low Risk): #10b981

## Component State Management

- Use React hooks (useState, useEffect)
- Props for data passing
- Context API for complex state (future)
- No Redux/Zustand for this scaffold

## API Integration

See `lib/api.ts` for all API calls:

```typescript
import { submitPatientIntake, fetchQueue } from '@/lib/api'

// Usage
const result = await submitPatientIntake(formData)
const queue = await fetchQueue()
```

## Adding New Components

1. Create file in `components/`
2. Use TypeScript interfaces for props
3. Add Tailwind classes
4. Export component
5. Import in pages

Example:
```typescript
interface MyComponentProps {
  title: string
  onChange: (value: string) => void
}

export default function MyComponent({ title, onChange }: MyComponentProps) {
  return <div className="..."> {title} </div>
}
```

## Performance Tips

- Use next/Image for images
- Code split with dynamic imports
- Use loading states for API calls
- Memoize expensive components with React.memo
- Optimize bundle with tree-shaking

## Common Issues

**API Connection Errors**
- Check NEXT_PUBLIC_API_URL in .env.local
- Verify backend is running on correct port
- Check CORS configuration

**Styling Issues**
- Rebuild Tailwind: `npm run build`
- Clear .next folder: `rm -rf .next`
- Check class names: Tailwind requires exact matches
