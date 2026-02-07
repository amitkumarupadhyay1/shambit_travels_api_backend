# Frontend Implementation Roadmap: Experiences Feature

## 🎯 Executive Summary

**Current State:** Backend fully functional, frontend has basic integration but missing critical customer-facing pages.

**Goal:** Build complete user experience for browsing, customizing, and booking packages with experiences.

**Timeline:** 2-4 weeks for MVP, 6-8 weeks for full feature set.

**Priority:** HIGH - Blocking customer bookings and revenue generation.

---

## 📋 Missing Components Analysis

### Critical (Blocking Revenue) - Week 1-2

1. **Package Detail Page** (`/packages/[slug]`)
   - Status: ❌ Does not exist
   - Impact: Customers cannot view package details or book
   - Effort: 3-4 days
   - Priority: P0

2. **Experience Selection Interface**
   - Status: ❌ Does not exist
   - Impact: Cannot customize packages
   - Effort: 2-3 days
   - Priority: P0

3. **Real-time Price Calculator**
   - Status: ❌ Does not exist
   - Impact: No pricing transparency
   - Effort: 1-2 days
   - Priority: P0

### Important (User Experience) - Week 3-4

4. **Packages Listing Page** (`/packages`)
   - Status: ❌ Does not exist
   - Impact: Cannot browse all packages
   - Effort: 2-3 days
   - Priority: P1

5. **Experience Detail Modal**
   - Status: ❌ Does not exist
   - Impact: Limited information for decision-making
   - Effort: 1-2 days
   - Priority: P1

6. **Package Comparison Tool**
   - Status: ❌ Does not exist
   - Impact: Harder to choose between options
   - Effort: 2-3 days
   - Priority: P2

### Nice-to-Have (Enhancement) - Week 5-8

7. **Interactive Package Builder**
   - Status: ❌ Does not exist
   - Impact: Less engaging experience
   - Effort: 4-5 days
   - Priority: P3

8. **Experience Reviews & Ratings**
   - Status: ❌ Does not exist (backend also needed)
   - Impact: Less social proof
   - Effort: 3-4 days
   - Priority: P3

---

## 🏗️ Implementation Plan

### Phase 1: MVP (Week 1-2) - Critical Path

#### 1.1 Package Detail Page

**File:** `frontend/shambit-frontend/src/app/packages/[slug]/page.tsx`

**Components Needed:**
```
PackageDetailPage/
├── PackageHeader (name, city, price range)
├── PackageGallery (images carousel)
├── PackageDescription (full description)
├── ExperienceSelector (checkbox list)
├── HotelTierSelector (radio buttons)
├── TransportSelector (radio buttons)
├── PriceCalculator (real-time pricing)
├── BookingButton (CTA)
└── PackageHighlights (key features)
```

**API Calls:**
```typescript
// Fetch package details
const package = await apiService.getPackage(slug);

// Calculate price on selection change
const price = await apiService.calculatePrice(slug, {
  experience_ids: selectedExperiences,
  hotel_tier_id: selectedHotel,
  transport_option_id: selectedTransport
});
```

**State Management:**
```typescript
const [selectedExperiences, setSelectedExperiences] = useState<number[]>([]);
const [selectedHotel, setSelectedHotel] = useState<number | null>(null);
const [selectedTransport, setSelectedTransport] = useState<number | null>(null);
const [calculatedPrice, setCalculatedPrice] = useState<number | null>(null);
const [isCalculating, setIsCalculating] = useState(false);
```

**User Flow:**
1. User lands on package detail page
2. Sees package info and all available options
3. Selects experiences (checkboxes)
4. Chooses hotel tier (radio)
5. Picks transport option (radio)
6. Price updates in real-time
7. Clicks "Book Now" → Booking flow

**Code Structure:**
```typescript
// src/app/packages/[slug]/page.tsx
export default async function PackageDetailPage({ 
  params 
}: { 
  params: { slug: string } 
}) {
  // Server-side data fetching
  const packageData = await apiService.getPackage(params.slug);
  
  return (
    <main>
      <PackageDetailClient packageData={packageData} />
    </main>
  );
}

// src/components/packages/PackageDetailClient.tsx
'use client';
export function PackageDetailClient({ packageData }) {
  // Client-side interactivity
  const [selections, setSelections] = useState({...});
  
  return (
    <div className="container">
      <PackageHeader package={packageData} />
      <ExperienceSelector 
        experiences={packageData.experiences}
        selected={selections.experiences}
        onChange={handleExperienceChange}
      />
      <PriceCalculator 
        selections={selections}
        packageSlug={packageData.slug}
      />
      <BookingButton />
    </div>
  );
}
```

#### 1.2 Experience Selector Component

**File:** `frontend/shambit-frontend/src/components/packages/ExperienceSelector.tsx`

**Features:**
- Checkbox for each experience
- Experience card with image, name, description, price
- Visual feedback on selection
- "Select All" / "Clear All" buttons
- Recommended combinations highlighted

**Code Example:**
```typescript
interface ExperienceSelectorProps {
  experiences: Experience[];
  selected: number[];
  onChange: (ids: number[]) => void;
}

export function ExperienceSelector({ 
  experiences, 
  selected, 
  onChange 
}: ExperienceSelectorProps) {
  const handleToggle = (id: number) => {
    if (selected.includes(id)) {
      onChange(selected.filter(x => x !== id));
    } else {
      onChange([...selected, id]);
    }
  };

  return (
    <div className="space-y-4">
      <h3 className="text-2xl font-semibold">Select Your Experiences</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {experiences.map(exp => (
          <ExperienceCard
            key={exp.id}
            experience={exp}
            selected={selected.includes(exp.id)}
            onToggle={() => handleToggle(exp.id)}
          />
        ))}
      </div>
    </div>
  );
}
```

#### 1.3 Real-time Price Calculator

**File:** `frontend/shambit-frontend/src/components/packages/PriceCalculator.tsx`

**Features:**
- Sticky sidebar showing current price
- Breakdown: experiences + hotel + transport
- Applied discounts/markups
- "Book Now" button
- Loading state during calculation

**Code Example:**
```typescript
export function PriceCalculator({ 
  selections, 
  packageSlug 
}: PriceCalculatorProps) {
  const [price, setPrice] = useState<PriceBreakdown | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const calculatePrice = async () => {
      if (!isValidSelection(selections)) return;
      
      setLoading(true);
      try {
        const result = await apiService.calculatePrice(packageSlug, {
          experience_ids: selections.experiences,
          hotel_tier_id: selections.hotel,
          transport_option_id: selections.transport
        });
        setPrice(result);
      } catch (error) {
        console.error('Price calculation failed:', error);
      } finally {
        setLoading(false);
      }
    };

    // Debounce to avoid too many API calls
    const timer = setTimeout(calculatePrice, 500);
    return () => clearTimeout(timer);
  }, [selections, packageSlug]);

  return (
    <div className="sticky top-20 bg-white rounded-lg shadow-lg p-6">
      <h3 className="text-xl font-semibold mb-4">Your Package</h3>
      
      {loading ? (
        <div className="animate-pulse">Loading...</div>
      ) : price ? (
        <>
          <PriceBreakdown breakdown={price.breakdown} />
          <div className="text-3xl font-bold text-orange-600 mt-4">
            ₹{price.total_price}
          </div>
          <button className="w-full mt-4 bg-orange-600 text-white py-3 rounded-lg">
            Book Now
          </button>
        </>
      ) : (
        <div className="text-gray-500">
          Select experiences to see price
        </div>
      )}
    </div>
  );
}
```

#### 1.4 API Service Updates

**File:** `frontend/shambit-frontend/src/lib/api.ts`

**Add Missing Methods:**
```typescript
class ApiService {
  // ... existing methods ...

  // Get single package by slug
  async getPackage(slug: string): Promise<Package> {
    return this.fetchApi<Package>(`/packages/packages/${slug}/`);
  }

  // Calculate package price
  async calculatePrice(
    slug: string, 
    selections: {
      experience_ids: number[];
      hotel_tier_id: number;
      transport_option_id: number;
    }
  ): Promise<PriceCalculation> {
    return this.fetchApi<PriceCalculation>(
      `/packages/packages/${slug}/calculate_price/`,
      {
        method: 'POST',
        body: JSON.stringify(selections),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAuthToken()}` // If required
        }
      }
    );
  }

  // Get price range
  async getPriceRange(slug: string): Promise<PriceRange> {
    return this.fetchApi<PriceRange>(
      `/packages/packages/${slug}/price_range/`
    );
  }
}

// Add TypeScript interfaces
export interface PriceCalculation {
  total_price: string;
  currency: string;
  breakdown: {
    experiences: Array<{
      id: number;
      name: string;
      price: string;
    }>;
    hotel_tier: {
      id: number;
      name: string;
      price_multiplier: string;
    };
    transport: {
      id: number;
      name: string;
      price: string;
    };
  };
  pricing_note: string;
}

export interface PriceRange {
  package: string;
  price_range: {
    min_price: string;
    max_price: string;
    currency: string;
  };
  note: string;
}
```

---

### Phase 2: Enhanced UX (Week 3-4)

#### 2.1 Packages Listing Page

**File:** `frontend/shambit-frontend/src/app/packages/page.tsx`

**Features:**
- Grid/list view toggle
- Filter by city (dropdown)
- Filter by price range (slider)
- Search by name
- Sort options (price, popularity, newest)
- Pagination
- Empty states

**Code Structure:**
```typescript
'use client';

export default function PackagesPage() {
  const [packages, setPackages] = useState<Package[]>([]);
  const [filters, setFilters] = useState({
    city: null,
    minPrice: 0,
    maxPrice: 100000,
    search: ''
  });
  const [sortBy, setSortBy] = useState('newest');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  return (
    <main className="container mx-auto py-12">
      <PackageFilters 
        filters={filters}
        onChange={setFilters}
      />
      
      <PackageSorter 
        sortBy={sortBy}
        onChange={setSortBy}
      />
      
      <ViewToggle 
        mode={viewMode}
        onChange={setViewMode}
      />
      
      <PackageGrid 
        packages={filteredPackages}
        viewMode={viewMode}
      />
      
      <Pagination 
        currentPage={page}
        totalPages={totalPages}
        onChange={setPage}
      />
    </main>
  );
}
```

#### 2.2 Experience Detail Modal

**File:** `frontend/shambit-frontend/src/components/packages/ExperienceDetailModal.tsx`

**Features:**
- Full description
- Image gallery
- Inclusions/exclusions list
- Duration and timing
- What to bring
- Important notes
- "Add to Package" button
- Reviews (future)

**Code Example:**
```typescript
export function ExperienceDetailModal({ 
  experience, 
  isOpen, 
  onClose,
  onAdd 
}: ExperienceDetailModalProps) {
  return (
    <Dialog open={isOpen} onClose={onClose}>
      <div className="max-w-4xl mx-auto">
        <ImageGallery images={experience.images} />
        
        <div className="p-6">
          <h2 className="text-3xl font-bold">{experience.name}</h2>
          <p className="text-2xl text-orange-600 mt-2">
            ₹{experience.base_price}
          </p>
          
          <div className="mt-6">
            <h3 className="text-xl font-semibold">Description</h3>
            <p className="mt-2">{experience.description}</p>
          </div>
          
          <div className="mt-6">
            <h3 className="text-xl font-semibold">What's Included</h3>
            <ul className="mt-2 space-y-2">
              {experience.inclusions?.map(item => (
                <li key={item} className="flex items-center">
                  <Check className="w-5 h-5 text-green-600 mr-2" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
          
          <button 
            onClick={onAdd}
            className="w-full mt-6 bg-orange-600 text-white py-3 rounded-lg"
          >
            Add to Package
          </button>
        </div>
      </div>
    </Dialog>
  );
}
```

---

### Phase 3: Advanced Features (Week 5-8)

#### 3.1 Interactive Package Builder

**File:** `frontend/shambit-frontend/src/app/package-builder/page.tsx`

**Features:**
- Step-by-step wizard
- Step 1: Choose destination
- Step 2: Select experiences
- Step 3: Choose hotel tier
- Step 4: Select transport
- Step 5: Review and book
- Progress indicator
- Save draft functionality
- Share package link

#### 3.2 Package Comparison Tool

**File:** `frontend/shambit-frontend/src/components/packages/PackageComparison.tsx`

**Features:**
- Compare up to 3 packages side-by-side
- Highlight differences
- Price comparison
- Experience comparison
- "Choose This" buttons

#### 3.3 Recommendation Engine

**File:** `frontend/shambit-frontend/src/components/packages/Recommendations.tsx`

**Features:**
- "Customers also selected"
- "Popular combinations"
- "Complete your experience with..."
- Based on booking patterns
- Personalized suggestions

---

## 🎨 Design System Components

### Reusable Components to Build

1. **ExperienceCard**
   - Compact view for lists
   - Expanded view for details
   - Selection state
   - Price badge
   - Image thumbnail

2. **PriceBreakdown**
   - Itemized list
   - Subtotals
   - Discounts/markups
   - Final total
   - Currency formatting

3. **SelectionSummary**
   - Sticky sidebar
   - Selected items list
   - Quick remove buttons
   - Total count
   - Total price

4. **PackageCard**
   - Grid view variant
   - List view variant
   - Hover effects
   - Quick actions
   - Price range display

5. **FilterPanel**
   - City selector
   - Price range slider
   - Search input
   - Sort dropdown
   - Clear filters button

---

## 🔧 Technical Requirements

### State Management

**Option 1: React Context (Recommended for MVP)**
```typescript
// src/contexts/PackageBuilderContext.tsx
export const PackageBuilderContext = createContext({
  selectedExperiences: [],
  selectedHotel: null,
  selectedTransport: null,
  calculatedPrice: null,
  // ... methods
});
```

**Option 2: Zustand (For complex state)**
```typescript
// src/stores/packageStore.ts
export const usePackageStore = create((set) => ({
  selections: {
    experiences: [],
    hotel: null,
    transport: null
  },
  setExperiences: (ids) => set((state) => ({
    selections: { ...state.selections, experiences: ids }
  })),
  // ... more actions
}));
```

### API Integration

**Authentication:**
- Check if `calculate_price` endpoint requires auth
- If yes, implement token management
- Handle 401 errors gracefully

**Error Handling:**
```typescript
try {
  const price = await apiService.calculatePrice(slug, selections);
  setPrice(price);
} catch (error) {
  if (error.status === 401) {
    // Redirect to login
    router.push('/login?redirect=' + currentPath);
  } else if (error.status === 400) {
    // Show validation errors
    setErrors(error.data.errors);
  } else {
    // Generic error
    toast.error('Failed to calculate price. Please try again.');
  }
}
```

**Loading States:**
- Skeleton loaders for package details
- Spinner for price calculation
- Disabled state for buttons during loading
- Optimistic UI updates where possible

### Performance Optimization

**Debouncing:**
```typescript
// Debounce price calculation to avoid excessive API calls
const debouncedCalculate = useMemo(
  () => debounce(calculatePrice, 500),
  [calculatePrice]
);
```

**Caching:**
```typescript
// Cache package details
const { data: packageData, isLoading } = useSWR(
  `/packages/${slug}`,
  () => apiService.getPackage(slug),
  { revalidateOnFocus: false }
);
```

**Image Optimization:**
```typescript
// Use Next.js Image component
<Image
  src={experience.image}
  alt={experience.name}
  width={400}
  height={300}
  loading="lazy"
  placeholder="blur"
/>
```

---

## 📱 Responsive Design

### Breakpoints

```css
/* Mobile First Approach */
.experience-grid {
  grid-template-columns: 1fr; /* Mobile */
}

@media (min-width: 768px) {
  .experience-grid {
    grid-template-columns: repeat(2, 1fr); /* Tablet */
  }
}

@media (min-width: 1024px) {
  .experience-grid {
    grid-template-columns: repeat(3, 1fr); /* Desktop */
  }
}
```

### Mobile Considerations

- Sticky price calculator at bottom on mobile
- Collapsible filter panel
- Swipeable experience cards
- Touch-friendly checkboxes (larger hit areas)
- Bottom sheet for experience details

---

## ✅ Testing Checklist

### Unit Tests

- [ ] ExperienceSelector component
- [ ] PriceCalculator component
- [ ] API service methods
- [ ] Utility functions (formatCurrency, etc.)

### Integration Tests

- [ ] Package detail page loads correctly
- [ ] Experience selection updates price
- [ ] Hotel/transport selection works
- [ ] Booking button navigates correctly

### E2E Tests (Playwright/Cypress)

- [ ] User can browse packages
- [ ] User can select experiences
- [ ] Price calculates correctly
- [ ] User can complete booking flow
- [ ] Error states display properly

### Manual Testing

- [ ] Test on Chrome, Firefox, Safari
- [ ] Test on mobile devices (iOS, Android)
- [ ] Test with slow network (throttling)
- [ ] Test with screen readers (accessibility)
- [ ] Test with different data scenarios

---

## 🚀 Deployment Checklist

### Pre-Deployment

- [ ] All tests passing
- [ ] No console errors
- [ ] Lighthouse score > 90
- [ ] Accessibility audit passed
- [ ] SEO meta tags added
- [ ] Analytics tracking implemented
- [ ] Error monitoring setup (Sentry)

### Environment Variables

```env
# .env.production
NEXT_PUBLIC_API_URL=https://api.shambit.com/api
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_SENTRY_DSN=your-sentry-dsn
```

### Monitoring

- [ ] Setup error tracking
- [ ] Monitor API response times
- [ ] Track conversion funnel
- [ ] Monitor page load times
- [ ] Setup alerts for errors

---

## 📊 Success Metrics

### Key Performance Indicators

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Page Load Time** | < 2s | Lighthouse, Web Vitals |
| **Time to Interactive** | < 3s | Lighthouse |
| **Conversion Rate** | > 5% | Analytics |
| **Avg Experiences Selected** | 3-4 | Backend analytics |
| **Price Calculator Usage** | > 80% | Event tracking |
| **Mobile Bounce Rate** | < 40% | Analytics |

### User Behavior Tracking

```typescript
// Track experience selection
analytics.track('Experience Selected', {
  experience_id: exp.id,
  experience_name: exp.name,
  package_slug: packageSlug,
  price: exp.base_price
});

// Track price calculation
analytics.track('Price Calculated', {
  package_slug: packageSlug,
  total_price: price.total_price,
  num_experiences: selections.experiences.length
});

// Track booking initiation
analytics.track('Booking Started', {
  package_slug: packageSlug,
  total_price: price.total_price
});
```

---

## 🎯 Implementation Timeline

### Week 1: Foundation
- **Day 1-2**: Setup package detail page structure
- **Day 3-4**: Build experience selector component
- **Day 5**: Implement price calculator

### Week 2: Integration
- **Day 1-2**: Connect all components
- **Day 3**: Add loading/error states
- **Day 4**: Implement responsive design
- **Day 5**: Testing and bug fixes

### Week 3: Enhancement
- **Day 1-2**: Build packages listing page
- **Day 3-4**: Add filtering and sorting
- **Day 5**: Create experience detail modal

### Week 4: Polish
- **Day 1-2**: Performance optimization
- **Day 3**: Accessibility improvements
- **Day 4**: Final testing
- **Day 5**: Deployment

---

## 🔗 Resources

### Documentation
- Next.js App Router: https://nextjs.org/docs/app
- Framer Motion: https://www.framer.com/motion/
- Tailwind CSS: https://tailwindcss.com/docs

### Backend API
- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- API Schema: `/api/schema/`

### Design Assets
- Figma: [Link to design files]
- Brand Guidelines: [Link to brand guide]
- Component Library: [Link to Storybook]

---

**Next Steps:**
1. Review this roadmap with team
2. Prioritize Phase 1 components
3. Assign tasks to developers
4. Setup project tracking (Jira/Linear)
5. Begin implementation

**Questions?** Contact: dev@shambit.com

---

**Document Version:** 1.0  
**Last Updated:** February 7, 2026  
**Status:** Ready for Implementation
