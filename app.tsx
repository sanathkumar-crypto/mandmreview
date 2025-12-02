import { useState } from 'react';
import { Header } from './components/Header';
import { PatientInfo } from './components/PatientInfo';
import { TimelineTable, TimelineEvent } from './components/TimelineTable';

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(true);

  // Mock patient data
  const patientData = {
    name: 'Thompson, Robert M.',
    mrn: 'MRN-2847563',
    dob: '03/15/1967',
    age: 58,
    gender: 'Male',
    admission: '11/25/2025 14:30',
    diagnosis: 'Acute Coronary Syndrome, Pneumonia',
  };

  // Generate mock timeline events with different timestamps
  const timelineEvents: TimelineEvent[] = [
    // Day 1 - Admission
    {
      timestamp: new Date('2025-11-25T14:30:00'),
      type: 'note',
      data: {
        author: 'Dr. Anderson (ED)',
        content: 'Patient presented with chest pain and shortness of breath. Initial assessment shows signs of ACS. Admitted for further evaluation.',
      },
    },
    {
      timestamp: new Date('2025-11-25T14:45:00'),
      type: 'vital',
      data: {
        bp: '145/92',
        hr: '102',
        temp: '99.1',
        rr: '22',
        spo2: '94',
      },
    },
    {
      timestamp: new Date('2025-11-25T15:00:00'),
      type: 'order',
      data: {
        type: 'Medication',
        details: 'Aspirin 325mg PO, Nitroglycerin 0.4mg SL PRN',
        orderedBy: 'Dr. Anderson',
      },
    },
    {
      timestamp: new Date('2025-11-25T15:30:00'),
      type: 'lab',
      data: {
        test: 'Cardiac Panel',
        results: {
          'Troponin I': '0.8 ng/mL (↑)',
          'CK-MB': '18 ng/mL (↑)',
          'BNP': '450 pg/mL',
        },
      },
    },
    {
      timestamp: new Date('2025-11-25T16:00:00'),
      type: 'io',
      data: {
        input: 'IV NS 500mL',
        output: 'Urine 200mL',
      },
    },
    
    // Day 1 - Evening
    {
      timestamp: new Date('2025-11-25T20:00:00'),
      type: 'vital',
      data: {
        bp: '138/88',
        hr: '95',
        temp: '98.8',
        rr: '20',
        spo2: '96',
      },
    },
    {
      timestamp: new Date('2025-11-25T20:30:00'),
      type: 'note',
      data: {
        author: 'Dr. Martinez (Cardiology)',
        content: 'Cardiology consult: Elevated troponins consistent with NSTEMI. Recommend cardiac catheterization tomorrow AM. Started on dual antiplatelet therapy.',
      },
    },
    {
      timestamp: new Date('2025-11-25T21:00:00'),
      type: 'order',
      data: {
        type: 'Procedure',
        details: 'Cardiac catheterization scheduled for 11/26 08:00',
        orderedBy: 'Dr. Martinez',
      },
    },
    
    // Day 2 - Morning
    {
      timestamp: new Date('2025-11-26T06:00:00'),
      type: 'vital',
      data: {
        bp: '132/84',
        hr: '88',
        temp: '98.6',
        rr: '18',
        spo2: '97',
      },
    },
    {
      timestamp: new Date('2025-11-26T06:30:00'),
      type: 'lab',
      data: {
        test: 'CBC',
        results: {
          'WBC': '12.5 K/μL (↑)',
          'Hgb': '13.2 g/dL',
          'Plt': '245 K/μL',
        },
      },
    },
    {
      timestamp: new Date('2025-11-26T07:00:00'),
      type: 'io',
      data: {
        input: 'PO fluids 240mL',
        output: 'Urine 350mL',
      },
    },
    {
      timestamp: new Date('2025-11-26T08:00:00'),
      type: 'note',
      data: {
        author: 'Dr. Chen (Interventional)',
        content: 'Cardiac cath performed. 80% stenosis in LAD. Successful PCI with drug-eluting stent placement. Patient tolerated procedure well.',
      },
    },
    {
      timestamp: new Date('2025-11-26T12:00:00'),
      type: 'vital',
      data: {
        bp: '128/80',
        hr: '82',
        temp: '99.2',
        rr: '19',
        spo2: '98',
      },
    },
    
    // Day 2 - Afternoon
    {
      timestamp: new Date('2025-11-26T14:00:00'),
      type: 'lab',
      data: {
        test: 'Chest X-Ray',
        results: {
          'Findings': 'Right lower lobe infiltrate',
          'Impression': 'Community-acquired pneumonia',
        },
      },
    },
    {
      timestamp: new Date('2025-11-26T14:30:00'),
      type: 'note',
      data: {
        author: 'Dr. Patel (Pulmonology)',
        content: 'Pulmonary consult: CXR shows RLL pneumonia. Patient has productive cough and fever. Will start broad-spectrum antibiotics.',
      },
    },
    {
      timestamp: new Date('2025-11-26T15:00:00'),
      type: 'order',
      data: {
        type: 'Medication',
        details: 'Ceftriaxone 2g IV q24h, Azithromycin 500mg PO daily',
        orderedBy: 'Dr. Patel',
      },
    },
    {
      timestamp: new Date('2025-11-26T18:00:00'),
      type: 'vital',
      data: {
        bp: '130/82',
        hr: '78',
        temp: '100.2',
        rr: '20',
        spo2: '95',
      },
    },
    {
      timestamp: new Date('2025-11-26T20:00:00'),
      type: 'io',
      data: {
        input: 'IV NS 1000mL, PO 480mL',
        output: 'Urine 650mL',
      },
    },
    
    // Day 3
    {
      timestamp: new Date('2025-11-27T06:00:00'),
      type: 'vital',
      data: {
        bp: '125/78',
        hr: '76',
        temp: '99.5',
        rr: '18',
        spo2: '97',
      },
    },
    {
      timestamp: new Date('2025-11-27T07:00:00'),
      type: 'lab',
      data: {
        test: 'Metabolic Panel',
        results: {
          'Na': '138 mEq/L',
          'K': '4.2 mEq/L',
          'Cr': '1.1 mg/dL',
          'BUN': '18 mg/dL',
        },
      },
    },
    {
      timestamp: new Date('2025-11-27T09:00:00'),
      type: 'note',
      data: {
        author: 'Dr. Anderson (Hospitalist)',
        content: 'Patient improving. Chest pain resolved. Respiratory symptoms improving on antibiotics. Plan to continue current management.',
      },
    },
    {
      timestamp: new Date('2025-11-27T12:00:00'),
      type: 'io',
      data: {
        input: 'PO fluids 720mL',
        output: 'Urine 580mL',
      },
    },
    {
      timestamp: new Date('2025-11-27T18:00:00'),
      type: 'vital',
      data: {
        bp: '122/76',
        hr: '72',
        temp: '98.9',
        rr: '16',
        spo2: '98',
      },
    },
    
    // Day 4
    {
      timestamp: new Date('2025-11-28T08:00:00'),
      type: 'note',
      data: {
        author: 'Dr. Martinez (Cardiology)',
        content: 'Follow-up: Patient stable post-PCI. Echo shows preserved EF 55%. Cleared for discharge with outpatient cardiac rehab.',
      },
    },
    {
      timestamp: new Date('2025-11-28T10:00:00'),
      type: 'order',
      data: {
        type: 'Discharge',
        details: 'Discharge to home. Follow-up in cardiology clinic in 2 weeks. Continue medications as prescribed.',
        orderedBy: 'Dr. Martinez',
      },
    },
    {
      timestamp: new Date('2025-11-28T10:30:00'),
      type: 'vital',
      data: {
        bp: '120/75',
        hr: '70',
        temp: '98.6',
        rr: '16',
        spo2: '99',
      },
    },
  ];

  const handleLogout = () => {
    setIsLoggedIn(false);
    alert('Logged out successfully');
  };

  if (!isLoggedIn) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#f8f9fa' }}>
        <div className="bg-white p-8 rounded-lg shadow-lg text-center">
          <h2 className="mb-4">You have been logged out</h2>
          <button
            onClick={() => setIsLoggedIn(true)}
            className="px-6 py-2 rounded-lg text-white"
            style={{ backgroundColor: 'var(--primary-blue)' }}
          >
            Login Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#f8f9fa' }}>
      <Header onLogout={handleLogout} />
      
      <main className="max-w-full px-6 py-6">
        <PatientInfo patient={patientData} />
        
        <div className="mb-4">
          <h2 style={{ color: 'var(--primary-dark-blue)' }}>
            Chronological Patient Timeline
          </h2>
          <p className="text-sm opacity-70 mt-1">
            All events displayed in chronological order for M&M review
          </p>
        </div>
        
        <TimelineTable events={timelineEvents} />
      </main>
    </div>
  );
}
