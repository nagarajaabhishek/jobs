import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface FAQItem {
    question: string;
    answer: string;
}

interface FAQProps {
    title: string;
    items: FAQItem[];
}

export default function FAQ({ title, items }: FAQProps) {
    const [openIndex, setOpenIndex] = useState<number | null>(0);

    return (
        <section className="faq-section">
            <div className="container">
                <div className="section-header text-center animate-fade-up">
                    <h2 className="text-gradient">{title}</h2>
                    <p className="subtitle">Everything you need to know about JobsProof.</p>
                </div>

                <div className="faq-grid animate-fade-up delay-1">
                    {items.map((item, idx) => (
                        <div key={idx} className="faq-item">
                            <button
                                className="faq-question"
                                onClick={() => setOpenIndex(openIndex === idx ? null : idx)}
                            >
                                <span>{item.question}</span>
                                {openIndex === idx ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                            </button>
                            {openIndex === idx && (
                                <div className="faq-answer animate-fade-in">
                                    {item.answer}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}
