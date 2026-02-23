# Frontend Integration Guide - Vehicle Optimization

## 🎨 UI/UX Design Specifications

### Overview
The vehicle selection optimization should be integrated into the booking flow as a **smart recommendation system** that helps users choose the most efficient vehicle combination for their group size.

---

## 📱 User Flow

### Step 1: Package Selection
User selects package, experiences, hotel tier, and enters travel dates.

### Step 2: Traveler Information
User enters number of travelers and optionally their details (names, ages).

### Step 3: Vehicle Selection (NEW - OPTIMIZED)
**This is where the optimization kicks in:**

```
┌─────────────────────────────────────────────────────────┐
│  🚗 Choose Your Transportation                          │
│                                                          │
│  For 10 travelers, 3 days                               │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │ ⭐ RECOMMENDED                                  │    │
│  │                                                 │    │
│  │  🚐 1 × Van (12 seats)                         │    │
│  │                                                 │    │
│  │  ✓ Seats: 12 (2 extra)                        │    │
│  │  ✓ Most economical                             │    │
│  │  ✓ Single vehicle convenience                  │    │
│  │                                                 │    │
│  │  ₹7,500 total (₹2,500/day × 3 days)           │    │
│  │                                                 │    │
│  │  [SELECT THIS OPTION] ←                        │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  Other Options:                                         │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  🚙 2 × SUV (7 seats each)                     │    │
│  │  Seats: 14 (4 extra)                           │    │
│  │  ₹9,000 total (₹3,000/day × 3 days)           │    │
│  │  [SELECT]                                       │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  🚗 3 × Sedan (4 seats each)                   │    │
│  │  Seats: 12 (2 extra)                           │    │
│  │  ₹9,000 total (₹3,000/day × 3 days)           │    │
│  │  [SELECT]                                       │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  💡 Tip: We've optimized these options for your        │
│     group size to minimize cost and unused seats.      │
└─────────────────────────────────────────────────────────┘
```

### Step 4: Review & Payment
Show selected vehicle combination in the booking summary.

---

## 💻 Implementation Examples

### React/Next.js Implementation

#### 1. API Hook
```typescript
// hooks/useVehicleSuggestions.ts
import { useState, useEffect } from 'react';

interface VehicleSuggestion {
  vehicles: Array<{
    transport_option_id: number;
    name: string;
    count: number;
    capacity: number;
    price_per_day: string;
  }>;
  total_vehicle_count: number;
  total_capacity: number;
  unused_seats: number;
  cost_per_day: string;
  total_cost: string;
  num_days: number;
  recommended: boolean;
}

interface VehicleSuggestionsResponse {
  passenger_count: number;
  num_days: number;
  solutions: VehicleSuggestion[];
}

export function useVehicleSuggestions(
  passengerCount: number,
  numDays: number,
  enabled: boolean = true
) {
  const [data, setData] = useState<VehicleSuggestionsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!enabled || passengerCount < 1 || numDays < 1) return;

    const fetchSuggestions = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch('/api/vehicle-suggestions/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            passenger_count: passengerCount,
            num_days: numDays,
            max_solutions: 5,
          }),
        });

        if (!response.ok) {
          throw new Error('Failed to fetch vehicle suggestions');
        }

        const result = await response.json();
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchSuggestions();
  }, [passengerCount, numDays, enabled]);

  return { data, loading, error };
}
```

#### 2. Vehicle Selection Component
```typescript
// components/VehicleSelection.tsx
import React, { useState } from 'react';
import { useVehicleSuggestions } from '@/hooks/useVehicleSuggestions';

interface VehicleSelectionProps {
  passengerCount: number;
  numDays: number;
  onSelect: (allocation: any) => void;
}

export function VehicleSelection({
  passengerCount,
  numDays,
  onSelect,
}: VehicleSelectionProps) {
  const { data, loading, error } = useVehicleSuggestions(passengerCount, numDays);
  const [selectedIndex, setSelectedIndex] = useState<number>(0);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
        <p className="ml-4 text-gray-600">Finding best vehicle options...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">⚠️ {error}</p>
      </div>
    );
  }

  if (!data || data.solutions.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-yellow-800">
          No vehicle options available for {passengerCount} travelers.
        </p>
      </div>
    );
  }

  const handleSelect = (index: number) => {
    setSelectedIndex(index);
    const solution = data.solutions[index];
    
    // Convert to vehicle_allocation format for booking
    const allocation = solution.vehicles.map(v => ({
      transport_option_id: v.transport_option_id,
      count: v.count,
    }));
    
    onSelect({
      vehicle_allocation: allocation,
      primary_transport_id: solution.vehicles[0].transport_option_id,
      total_cost: solution.total_cost,
    });
  };

  return (
    <div className="space-y-4">
      <div className="mb-6">
        <h3 className="text-xl font-semibold text-gray-900">
          🚗 Choose Your Transportation
        </h3>
        <p className="text-gray-600 mt-1">
          For {passengerCount} travelers, {numDays} days
        </p>
      </div>

      {data.solutions.map((solution, index) => (
        <VehicleOption
          key={index}
          solution={solution}
          isSelected={selectedIndex === index}
          isRecommended={solution.recommended}
          onSelect={() => handleSelect(index)}
        />
      ))}

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-6">
        <p className="text-sm text-blue-800">
          💡 <strong>Tip:</strong> We've optimized these options for your group size
          to minimize cost and unused seats.
        </p>
      </div>
    </div>
  );
}

interface VehicleOptionProps {
  solution: any;
  isSelected: boolean;
  isRecommended: boolean;
  onSelect: () => void;
}

function VehicleOption({
  solution,
  isSelected,
  isRecommended,
  onSelect,
}: VehicleOptionProps) {
  const getVehicleIcon = (name: string) => {
    const lower = name.toLowerCase();
    if (lower.includes('van')) return '🚐';
    if (lower.includes('suv')) return '🚙';
    if (lower.includes('sedan')) return '🚗';
    return '🚗';
  };

  return (
    <div
      className={`
        relative border-2 rounded-lg p-6 cursor-pointer transition-all
        ${isSelected 
          ? 'border-blue-600 bg-blue-50 shadow-lg' 
          : 'border-gray-200 bg-white hover:border-blue-300 hover:shadow-md'
        }
        ${isRecommended ? 'ring-2 ring-yellow-400' : ''}
      `}
      onClick={onSelect}
    >
      {isRecommended && (
        <div className="absolute -top-3 left-4 bg-yellow-400 text-yellow-900 px-3 py-1 rounded-full text-xs font-bold">
          ⭐ RECOMMENDED
        </div>
      )}

      <div className="flex items-start justify-between">
        <div className="flex-1">
          {/* Vehicle List */}
          <div className="space-y-2 mb-4">
            {solution.vehicles.map((vehicle: any, idx: number) => (
              <div key={idx} className="flex items-center text-lg font-medium">
                <span className="mr-2">{getVehicleIcon(vehicle.name)}</span>
                <span>
                  {vehicle.count} × {vehicle.name}
                  <span className="text-sm text-gray-500 ml-2">
                    ({vehicle.capacity} seats each)
                  </span>
                </span>
              </div>
            ))}
          </div>

          {/* Details */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Total Seats:</span>
              <span className="ml-2 font-medium">
                {solution.total_capacity}
                {solution.unused_seats > 0 && (
                  <span className="text-gray-500">
                    ({solution.unused_seats} extra)
                  </span>
                )}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Vehicles:</span>
              <span className="ml-2 font-medium">
                {solution.total_vehicle_count}
              </span>
            </div>
          </div>

          {/* Benefits */}
          {isRecommended && (
            <div className="mt-3 space-y-1">
              <div className="flex items-center text-sm text-green-700">
                <span className="mr-2">✓</span>
                <span>Most economical option</span>
              </div>
              {solution.total_vehicle_count === 1 && (
                <div className="flex items-center text-sm text-green-700">
                  <span className="mr-2">✓</span>
                  <span>Single vehicle convenience</span>
                </div>
              )}
              {solution.unused_seats <= 2 && (
                <div className="flex items-center text-sm text-green-700">
                  <span className="mr-2">✓</span>
                  <span>Minimal unused seats</span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Price */}
        <div className="text-right ml-6">
          <div className="text-2xl font-bold text-gray-900">
            ₹{parseFloat(solution.total_cost).toLocaleString()}
          </div>
          <div className="text-sm text-gray-600">
            ₹{solution.cost_per_day}/day × {solution.num_days} days
          </div>
        </div>
      </div>

      {/* Select Button */}
      <button
        className={`
          mt-4 w-full py-3 px-4 rounded-lg font-medium transition-colors
          ${isSelected
            ? 'bg-blue-600 text-white'
            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }
        `}
      >
        {isSelected ? '✓ SELECTED' : 'SELECT THIS OPTION'}
      </button>
    </div>
  );
}
```

#### 3. Integration in Booking Flow
```typescript
// pages/booking/[packageId].tsx
import { useState } from 'react';
import { VehicleSelection } from '@/components/VehicleSelection';

export default function BookingPage() {
  const [bookingData, setBookingData] = useState({
    packageId: 1,
    experienceIds: [1, 2],
    hotelTierId: 1,
    numTravelers: 10,
    bookingDate: '2024-06-01',
    bookingEndDate: '2024-06-04',
    // Vehicle selection
    vehicleAllocation: null,
    primaryTransportId: null,
  });

  const numDays = calculateDays(bookingData.bookingDate, bookingData.bookingEndDate);

  const handleVehicleSelect = (vehicleData: any) => {
    setBookingData(prev => ({
      ...prev,
      vehicleAllocation: vehicleData.vehicle_allocation,
      primaryTransportId: vehicleData.primary_transport_id,
    }));
  };

  const handleSubmit = async () => {
    const response = await fetch('/api/bookings/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        'Idempotency-Key': generateIdempotencyKey(),
      },
      body: JSON.stringify({
        package_id: bookingData.packageId,
        experience_ids: bookingData.experienceIds,
        hotel_tier_id: bookingData.hotelTierId,
        transport_option_id: bookingData.primaryTransportId,
        vehicle_allocation: bookingData.vehicleAllocation,
        num_travelers: bookingData.numTravelers,
        booking_date: bookingData.bookingDate,
        booking_end_date: bookingData.bookingEndDate,
        customer_name: 'John Doe',
        customer_email: 'john@example.com',
        customer_phone: '+1234567890',
      }),
    });

    if (response.ok) {
      const booking = await response.json();
      router.push(`/booking/${booking.id}/payment`);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Step 1: Package Info */}
      <PackageInfo packageId={bookingData.packageId} />

      {/* Step 2: Traveler Info */}
      <TravelerInfo
        numTravelers={bookingData.numTravelers}
        onChange={(num) => setBookingData(prev => ({ ...prev, numTravelers: num }))}
      />

      {/* Step 3: Vehicle Selection */}
      <VehicleSelection
        passengerCount={bookingData.numTravelers}
        numDays={numDays}
        onSelect={handleVehicleSelect}
      />

      {/* Step 4: Submit */}
      <button
        onClick={handleSubmit}
        disabled={!bookingData.vehicleAllocation}
        className="w-full mt-6 bg-blue-600 text-white py-4 rounded-lg font-semibold"
      >
        Continue to Payment
      </button>
    </div>
  );
}
```

---

## 🎨 Design Variations

### Variation 1: Card Grid Layout
```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ ⭐ BEST      │  │              │  │              │
│              │  │              │  │              │
│ 🚐 1 × Van   │  │ 🚙 2 × SUV   │  │ 🚗 3 × Sedan │
│              │  │              │  │              │
│ 12 seats     │  │ 14 seats     │  │ 12 seats     │
│ 2 extra      │  │ 4 extra      │  │ 2 extra      │
│              │  │              │  │              │
│ ₹7,500       │  │ ₹9,000       │  │ ₹9,000       │
│              │  │              │  │              │
│ [SELECT] ←   │  │ [SELECT]     │  │ [SELECT]     │
└──────────────┘  └──────────────┘  └──────────────┘
```

### Variation 2: Comparison Table
```
┌─────────────────────────────────────────────────────────┐
│ Option      │ Vehicles │ Seats │ Extra │ Cost    │      │
├─────────────────────────────────────────────────────────┤
│ ⭐ 1 × Van  │    1     │  12   │   2   │ ₹7,500  │ [✓]  │
│   2 × SUV   │    2     │  14   │   4   │ ₹9,000  │ [ ]  │
│   3 × Sedan │    3     │  12   │   2   │ ₹9,000  │ [ ]  │
└─────────────────────────────────────────────────────────┘
```

### Variation 3: Mobile-Optimized
```
┌─────────────────────────────┐
│ 🚗 Transportation           │
│                             │
│ For 10 travelers, 3 days    │
│                             │
│ ┌─────────────────────────┐ │
│ │ ⭐ RECOMMENDED          │ │
│ │                         │ │
│ │ 🚐 1 × Van              │ │
│ │ 12 seats (2 extra)      │ │
│ │                         │ │
│ │ ₹7,500 total            │ │
│ │                         │ │
│ │ [SELECT] ←              │ │
│ └─────────────────────────┘ │
│                             │
│ [Show 2 more options ▼]    │
└─────────────────────────────┘
```

---

## 📊 Booking Summary Display

### In Review Page
```
┌─────────────────────────────────────────────────────────┐
│ Booking Summary                                         │
├─────────────────────────────────────────────────────────┤
│ Package: Goa Beach Adventure                            │
│ Dates: Jun 1-4, 2024 (3 nights)                        │
│ Travelers: 10 people                                    │
│                                                          │
│ Transportation:                                         │
│   🚐 1 × Van (12 seats)                                │
│   ₹2,500/day × 3 days = ₹7,500                         │
│                                                          │
│ Hotel: Deluxe (3 rooms)                                │
│   ₹5,000/night × 3 nights = ₹15,000                    │
│                                                          │
│ Experiences:                                            │
│   • Beach Parasailing                                   │
│   • Sunset Cruise                                       │
│                                                          │
│ ─────────────────────────────────────────────────────── │
│ Total: ₹45,000                                          │
│                                                          │
│ [PROCEED TO PAYMENT]                                    │
└─────────────────────────────────────────────────────────┘
```

### In Confirmation Email
```
Your Booking Confirmation - #SB-2024-000123

Transportation Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚐 1 × Van (12-seater)
   • Capacity: 12 passengers
   • Your group: 10 travelers
   • Duration: 3 days
   • Cost: ₹7,500

This vehicle will be available for your entire trip from
June 1-4, 2024.

Driver contact will be shared 24 hours before your trip.
```

---

## 🔄 State Management

### Redux/Zustand Store
```typescript
// store/bookingSlice.ts
interface BookingState {
  vehicleSuggestions: VehicleSuggestion[] | null;
  selectedVehicleIndex: number;
  vehicleAllocation: any | null;
  loadingSuggestions: boolean;
}

const bookingSlice = createSlice({
  name: 'booking',
  initialState: {
    vehicleSuggestions: null,
    selectedVehicleIndex: 0,
    vehicleAllocation: null,
    loadingSuggestions: false,
  },
  reducers: {
    setVehicleSuggestions: (state, action) => {
      state.vehicleSuggestions = action.payload;
      state.selectedVehicleIndex = 0; // Auto-select recommended
    },
    selectVehicle: (state, action) => {
      state.selectedVehicleIndex = action.payload;
      const solution = state.vehicleSuggestions?.[action.payload];
      if (solution) {
        state.vehicleAllocation = solution.vehicles.map(v => ({
          transport_option_id: v.transport_option_id,
          count: v.count,
        }));
      }
    },
    clearVehicleSelection: (state) => {
      state.vehicleSuggestions = null;
      state.selectedVehicleIndex = 0;
      state.vehicleAllocation = null;
    },
  },
});
```

---

## ⚠️ Error Handling

### No Vehicles Available
```typescript
if (!data || data.solutions.length === 0) {
  return (
    <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
      <div className="flex">
        <div className="flex-shrink-0">
          <svg className="h-5 w-5 text-yellow-400" /* ... */ />
        </div>
        <div className="ml-3">
          <p className="text-sm text-yellow-700">
            <strong>No vehicles available</strong> for {passengerCount} travelers.
            Please contact support or adjust your group size.
          </p>
          <button className="mt-2 text-sm text-yellow-800 underline">
            Contact Support
          </button>
        </div>
      </div>
    </div>
  );
}
```

### API Error
```typescript
if (error) {
  return (
    <div className="bg-red-50 border-l-4 border-red-400 p-4">
      <div className="flex">
        <div className="flex-shrink-0">
          <svg className="h-5 w-5 text-red-400" /* ... */ />
        </div>
        <div className="ml-3">
          <p className="text-sm text-red-700">
            <strong>Error loading vehicle options.</strong> {error}
          </p>
          <button 
            onClick={retry}
            className="mt-2 text-sm text-red-800 underline"
          >
            Try Again
          </button>
        </div>
      </div>
    </div>
  );
}
```

### Passenger Count Changed
```typescript
useEffect(() => {
  if (passengerCountChanged) {
    // Clear previous selection
    setSelectedVehicle(null);
    
    // Show warning
    toast.warning(
      'Passenger count changed. Please select vehicles again.',
      { duration: 5000 }
    );
  }
}, [passengerCount]);
```

---

## 📱 Responsive Design

### Mobile (< 640px)
- Stack vehicle options vertically
- Show 1 option at a time with "Show more" button
- Simplified details (hide extra info)
- Large touch targets (min 44px)

### Tablet (640px - 1024px)
- 2 columns for vehicle options
- Show top 4 options
- Collapsible details

### Desktop (> 1024px)
- 3 columns or list view
- Show all options
- Hover effects
- Comparison mode

---

## 🎯 Best Practices

### 1. Auto-Select Recommended
```typescript
useEffect(() => {
  if (data?.solutions && data.solutions.length > 0) {
    // Auto-select the recommended option
    handleSelect(0);
  }
}, [data]);
```

### 2. Show Loading State
```typescript
{loading && (
  <div className="flex items-center justify-center p-8">
    <Spinner />
    <p>Finding best options for your group...</p>
  </div>
)}
```

### 3. Validate Before Submit
```typescript
const canProceed = () => {
  return (
    bookingData.vehicleAllocation &&
    bookingData.vehicleAllocation.length > 0 &&
    bookingData.primaryTransportId
  );
};
```

### 4. Show Price Breakdown
```typescript
<div className="text-sm text-gray-600">
  {solution.vehicles.map(v => (
    <div key={v.transport_option_id}>
      {v.count} × {v.name}: ₹{v.price_per_day}/day
    </div>
  ))}
  <div className="border-t mt-2 pt-2 font-medium">
    Total: ₹{solution.cost_per_day}/day × {solution.num_days} days
    = ₹{solution.total_cost}
  </div>
</div>
```

### 5. Accessibility
```typescript
<button
  role="radio"
  aria-checked={isSelected}
  aria-label={`Select ${solution.vehicles.map(v => `${v.count} ${v.name}`).join(', ')}`}
  onClick={onSelect}
>
  {/* ... */}
</button>
```

---

## 🧪 Testing

### Unit Tests
```typescript
describe('VehicleSelection', () => {
  it('displays loading state', () => {
    render(<VehicleSelection passengerCount={10} numDays={3} />);
    expect(screen.getByText(/finding best/i)).toBeInTheDocument();
  });

  it('auto-selects recommended option', async () => {
    render(<VehicleSelection passengerCount={10} numDays={3} />);
    await waitFor(() => {
      expect(screen.getByText(/selected/i)).toBeInTheDocument();
    });
  });

  it('calls onSelect with correct data', async () => {
    const onSelect = jest.fn();
    render(
      <VehicleSelection 
        passengerCount={10} 
        numDays={3} 
        onSelect={onSelect}
      />
    );
    
    await waitFor(() => screen.getByText(/select/i));
    fireEvent.click(screen.getAllByText(/select/i)[0]);
    
    expect(onSelect).toHaveBeenCalledWith(
      expect.objectContaining({
        vehicle_allocation: expect.any(Array),
        primary_transport_id: expect.any(Number),
      })
    );
  });
});
```

---

## 📚 Additional Resources

- **API Documentation:** `/api/vehicle-suggestions/` endpoint
- **Backend Guide:** `VEHICLE_OPTIMIZATION_README.md`
- **Quick Start:** `QUICK_START_GUIDE.md`
- **Figma Designs:** [Link to design files]

---

**Questions?** Contact the frontend or backend team for assistance.
