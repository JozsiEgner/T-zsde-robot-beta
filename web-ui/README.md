# Dollar Thermometer UI

A komponens a feltöltött Civil Axis / Dollar Output Engine projekt kijelzőrétegéből készült önálló, újrahasznosítható React-modul.

## Fájlok

- `DollarThermometer.tsx`
- `DollarThermometer.css`

## Használat

```tsx
import DollarThermometer from "./web-ui/DollarThermometer";

<DollarThermometer
  direction="UP"
  signalScore={0.42}
  intensityScore={0.68}
  intensityLevel="MEDIUM"
  confidenceScore={0.81}
  difficultyFactor={0.27}
  difficultyLevel="LOW"
  sourceHealthScore={0.93}
/>
```

## Bemenetek

- `direction`: `UP`, `DOWN` vagy `NEUTRAL`
- `signalScore`: `-1..+1`
- `intensityScore`: `0..1`
- `confidenceScore`: `0..1`
- `difficultyFactor`: `0..1`
- `sourceHealthScore`: `0..1`

A komponens csak kijelző. Nem végez kereskedést és nem számít önálló piaci jelet.
