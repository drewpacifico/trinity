from flask import Flask, render_template, redirect, url_for, request, session
import re
from pathlib import Path
import markdown

app = Flask(__name__)
app.secret_key = 'freight-training-secret-key-2025'  # Required for session management

PROJECT_MD_PATH = Path(__file__).parent / "project.md"

# Quiz questions for Module 1.1
MODULE_1_1_QUIZ = [
    {
        "id": "q1_1_1",
        "question": "A potential customer asks why they should work with you instead of calling carriers directly. Which response best demonstrates your value proposition?",
        "choices": [
            "I can get you the cheapest rate possible every time",
            "I provide access to a network of carriers, handle logistics complexities, verify credentials, and save you time so you can focus on your core business",
            "I just pass along shipment information to carriers and collect a fee",
            "I only work with one exclusive carrier that gives the best service"
        ],
        "correct_index": 1,
        "explanation": "Your value proposition includes expertise, carrier network access, time savings, risk management through credential verification, and allowing customers to focus on their core business. You're a logistics consultant, not just a middleman or someone who only promises the cheapest rates."
    },
    {
        "id": "q1_1_2",
        "question": "Approximately what percentage of all freight tonnage in the United States moves by truck, and why does this matter to you as a freight agent?",
        "choices": [
            "50% - meaning trucking is one of several equally important freight methods",
            "70% - demonstrating that trucking is essential to the economy and your services facilitate critical operations",
            "30% - showing that most freight moves by rail and ship instead",
            "90% - proving that all other shipping methods are obsolete"
        ],
        "correct_index": 1,
        "explanation": "Approximately 70% of all freight tonnage moves by truck, making trucking essential to the American economy. This means the services you provide aren't optional extras—you're facilitating critical operations that businesses depend on."
    }
]

# Quiz questions for Module 1.2
MODULE_1_2_QUIZ = [
    {
        "id": "q1_2_1",
        "question": "The trucking industry generates approximately how much in annual revenue, and what does this scale mean for your career?",
        "choices": [
            "$200 billion - indicating a small, specialized market with limited opportunities",
            "$800+ billion - demonstrating a massive industry with substantial career opportunities",
            "$8 trillion - showing trucking is the largest industry in America",
            "$80 billion - suggesting a moderate-sized niche market"
        ],
        "correct_index": 1,
        "explanation": "The trucking industry generates over $800 billion in annual revenue, demonstrating a massive industry with substantial career opportunities. This scale shows there's significant room for successful freight agents who provide valuable services."
    }
]

# Quiz questions for Module 1.3
MODULE_1_3_QUIZ = [
    {
        "id": "q1_3_1",
        "question": "A shipper tells you they can get a load moved for $1,500 by calling a carrier directly. You can arrange it for $1,200 with a $300 commission. What should you emphasize in your response?",
        "choices": [
            "You should drop your commission to compete on price alone",
            "They save $300, you earn your commission, and the carrier gets a fair rate—everyone wins, plus they get your expertise and service",
            "Tell them to use the carrier directly since they found a better price",
            "Explain that your $1,500 price is actually better because it includes hidden fees they don't know about"
        ],
        "correct_index": 1,
        "explanation": "This is a perfect example of creating value for everyone. The shipper saves money ($300), you earn your commission ($300), and the carrier receives a fair rate. Plus, the shipper gets your expertise, carrier network access, and risk management—demonstrating that using a freight agent often provides better pricing along with superior service."
    },
    {
        "id": "q1_3_2",
        "question": "Which of the following best describes how you provide 'Risk Management' value to your customers?",
        "choices": [
            "You insure every shipment personally against damage or loss",
            "You verify carrier credentials, ensure proper insurance coverage, and help resolve issues—protecting clients from risks they might not know exist",
            "You only work with the three largest carriers to eliminate all risk",
            "You guarantee that nothing will ever go wrong with any shipment"
        ],
        "correct_index": 1,
        "explanation": "Risk management means verifying carrier credentials, ensuring proper insurance coverage, and helping resolve issues when problems arise. This due diligence protects your clients from risks they might not even know exist, such as working with carriers who have inadequate insurance or poor safety records."
    }
]

# Quiz questions for Module 1.4
MODULE_1_4_QUIZ = [
    {
        "id": "q1_4_1",
        "question": "You arrange a shipment where the customer pays $2,000 and the carrier receives $1,600, creating a $400 gross margin. With your compensation structure, what do you earn from this transaction?",
        "choices": [
            "You earn the full $2,000 customer payment",
            "You earn your base salary plus commission on the $400 margin",
            "You earn $400 total with no additional salary",
            "You earn a percentage of the $2,000 total revenue"
        ],
        "correct_index": 1,
        "explanation": "You earn your base salary plus commission on the $400 gross margin (the difference between what the customer pays and what the carrier receives). Your compensation structure provides income stability through base salary while rewarding performance through commissions on the margins you generate."
    },
    {
        "id": "q1_4_2",
        "question": "What is the key advantage of the salaried-plus-commission compensation structure compared to pure commission?",
        "choices": [
            "You make more total money with a salary than with pure commission",
            "You never have to work hard because the salary covers everything",
            "Your base salary provides financial stability while you build your customer base, removing the stress of variable income during the learning phase",
            "The commission is just a bonus and doesn't really matter to your income"
        ],
        "correct_index": 2,
        "explanation": "The base salary provides financial stability while you develop your book of business, removing the financial stress that purely commission-based roles create. This allows you to focus on building long-term relationships rather than desperate short-term tactics, while commission earnings reward your effectiveness and grow as you become more successful."
    }
]

# Quiz questions for Module 1.5
MODULE_1_5_QUIZ = [
    {
        "id": "q1_5_1",
        "question": "You're in Month 2 of your freight agent career. You've made very few shipments and commission earnings are minimal. What should be your primary focus and mindset?",
        "choices": [
            "Quit immediately because low earnings in Month 2 means you'll never succeed",
            "Focus on learning, mastering systems, and building your prospecting foundation—minimal commission during months 1-3 is normal and expected",
            "Pressure every prospect to book immediately to generate quick income",
            "Spend all your time looking for a different career",
        ],
        "correct_index": 1,
        "explanation": "During months 1-3 (Foundation Building phase), your focus should be on learning rather than earning. You'll spend significant time in training, studying industry practices, understanding systems, and developing prospecting skills. Your salary provides financial stability during this essential learning period. Minimal commission earnings during this phase are normal and expected."
    },
    {
        "id": "q1_5_2",
        "question": "During months 6-12 of your career, what key shift typically occurs that drives increased commission earnings?",
        "choices": [
            "You suddenly learn secret pricing techniques that double your margins",
            "Your earlier customers begin providing repeat business, your efficiency improves, and you have more time for business development as efforts compound",
            "The company automatically assigns you bigger customers",
            "Market conditions always improve during this timeframe"
        ],
        "correct_index": 1,
        "explanation": "During the Momentum Building phase (months 6-12), your efforts compound. Customers you secured earlier begin providing repeat business, your operational efficiency improves allowing more time for business development, commission earnings become more substantial as shipment volume increases and pricing skills sharpen. This is the natural result of consistent effort over time."
    },
    {
        "id": "q1_5_3",
        "question": "'The prospecting calls you make today produce customers 30-90 days from now.' What critical principle does this statement teach you?",
        "choices": [
            "You should wait 90 days before making any prospecting calls",
            "Effort precedes results—consistent daily activity is essential even when immediate results aren't visible",
            "Prospecting doesn't work until you've been in the business for 90 days",
            "You only need to prospect once every 30-90 days"
        ],
        "correct_index": 1,
        "explanation": "This illustrates the principle that effort precedes results. Your current income reflects efforts from previous months, not today's work. This means you must maintain consistent daily prospecting activity even when you don't see immediate results, because those efforts will produce customers and revenue 30-90 days in the future."
    }
]

# Quiz questions for Module 1.6
MODULE_1_6_QUIZ = [
    {
        "id": "q1_6_1",
        "question": "A shipment you arranged is running late due to carrier delays. The customer hasn't called yet. What does professionalism require you to do?",
        "choices": [
            "Wait for the customer to call and complain, then explain it's the carrier's fault",
            "Communicate proactively about the delay before they call, own the situation, and provide updates on resolution",
            "Ignore it and hope the customer doesn't notice",
            "Blame the carrier and tell the customer to contact them directly"
        ],
        "correct_index": 1,
        "explanation": "Professionalism requires proactive communication. When a shipment is running late, communicate proactively rather than waiting for angry phone calls. Own the situation, provide clear information, and update on resolution efforts. This builds trust even when problems occur, whereas hiding issues or deflecting blame destroys your reputation."
    },
    {
        "id": "q1_6_2",
        "question": "You can book a problematic load that you know will likely have issues, earning a quick $400 commission. What should you do?",
        "choices": [
            "Book it immediately—$400 is $400, and it's the customer's problem if issues arise",
            "Don't book loads you know are problematic just to earn commission—always act in your customer's best interest even when it costs you money short-term",
            "Book it but don't tell the customer about the potential problems",
            "Book it and blame any problems on the carrier later"
        ],
        "correct_index": 1,
        "explanation": "Ethical behavior means always acting in your customer's best interest, even when it costs you money in the short term. Don't book loads you know are problematic just to earn a commission. Ethical lapses might create short-term profits but destroy long-term success. Your reputation is your most valuable asset."
    },
    {
        "id": "q1_6_3",
        "question": "Why is treating everyone with respect—including small customers and every carrier—described as a 'strategic business decision' rather than just 'being nice'?",
        "choices": [
            "It's not strategic; it's just about being a good person with no business impact",
            "Small customers today may become large customers tomorrow; carriers you treat well will prioritize your freight when capacity is tight; reputation drives success in this relationship-based industry",
            "You're legally required to treat everyone equally by federal regulation",
            "It only matters for large customers; small customers and carriers don't impact your success"
        ],
        "correct_index": 1,
        "explanation": "Professionalism is a strategic business decision because relationships and reputation drive success in this industry. Small customers today might become large customers tomorrow. Carriers you treat well and pay promptly will prioritize your freight when capacity is tight. Drivers you respect will remember and accept your loads in the future. Your reputation is your competitive advantage."
    }
]

# Quiz questions for Module 2.1
MODULE_2_1_QUIZ = [
    {
        "id": "q2_1_1",
        "question": "A customer asks for a rush shipment and questions why the rate is higher than usual. How do you best explain this using your knowledge of the freight ecosystem?",
        "choices": [
            "Suggest they wait until rates go down next week",
            "Offer to find a cheaper carrier even if it means lower service quality",
            "Explain that tight capacity affects carriers who then demand premium rates, and you must pass those costs along—helping them understand market realities",
            "Tell them that's just how pricing works during busy times"
        ],
        "correct_index": 2,
        "explanation": "Understanding the ecosystem helps you educate customers about market realities. When capacity is tight, carriers can be selective and demand higher rates. Explaining this transforms you from someone who 'just quotes prices' into a consultant who helps customers understand the business dynamics affecting their shipping costs."
    },
    {
        "id": "q2_1_2",
        "question": "Why is understanding the freight ecosystem compared to 'understanding a city' in the training material?",
        "choices": [
            "Because cities are the only places where freight agents work",
            "Because freight only moves within cities, not between them",
            "Because both involve driving trucks through streets",
            "Just like knowing a city's neighborhoods helps you navigate effectively, knowing who the industry participants are and how they interact makes you more effective at solving logistics problems"
        ],
        "correct_index": 3,
        "explanation": "The analogy emphasizes that understanding the structure and relationships within the freight industry—who does what, how they interact, where you fit—makes you far more effective. You could operate without this knowledge, but understanding the ecosystem transforms you from a basic service provider into a knowledgeable consultant who can educate customers and navigate complex situations."
    }
]

# Quiz questions for Module 2.2
MODULE_2_2_QUIZ = [
    {
        "id": "q2_2_1",
        "question": "You're approaching a large manufacturer who has established carrier relationships. What's your best strategy?",
        "choices": [
            "Position yourself as their capacity supplement for peak seasons and backup situations when regular carriers are full",
            "Tell them their current carriers are probably unreliable",
            "Undercut their current carriers' rates by 30% to win the business",
            "Demand they give you all their freight immediately to prove your value"
        ],
        "correct_index": 0,
        "explanation": "Manufacturers have established relationships built over years. Trying to replace their primary carriers creates resistance. Instead, position yourself as a capacity supplement for peak seasons and backup situations. This reduces resistance and creates win-win opportunities where you provide value without threatening their existing relationships."
    }
]

# Quiz questions for Module 2.3
MODULE_2_3_QUIZ = [
    {
        "id": "q2_3_1",
        "question": "When should you use an owner-operator versus a large national carrier?",
        "choices": [
            "It doesn't matter—all carriers are the same",
            "Always use large carriers because they're safer",
            "Only use owner-operators because they're cheaper",
            "Use owner-operators for loads requiring special attention or white-glove service where you've built trust; use large carriers for high-volume customers requiring significant capacity"
        ],
        "correct_index": 3,
        "explanation": "Different carrier types serve different needs. Owner-operators often provide excellent personalized service for special-attention loads, especially on lanes where you've built relationships. Large national carriers offer capacity, geographic reach, and sophisticated systems for high-volume customers. Matching carrier type to shipment requirements is a key skill."
    }
]

# Quiz questions for Module 2.4
MODULE_2_4_QUIZ = [
    {
        "id": "q2_4_1",
        "question": "A freight forwarder contacts you about domestic trucking for an international shipment. What opportunity does this represent?",
        "choices": [
            "Forwarders only handle air freight, not trucking",
            "No opportunity—forwarders are competitors, not customers",
            "You should only work with direct shippers, never intermediaries",
            "Drayage movements (first and last mile) from shipper to port or port to final destination"
        ],
        "correct_index": 3,
        "explanation": "Freight forwarders specialize in international shipping but often need domestic trucking for first and last miles—moving freight from the shipper to the port, or from the port to the final destination. These 'drayage' movements create opportunities for freight agents who understand intermodal operations."
    }
]

# Quiz questions for Module 2.5
MODULE_2_5_QUIZ = [
    {
        "id": "q2_5_1",
        "question": "Before tendering a load to a carrier you found on a load board, what must you verify?",
        "choices": [
            "Active FMCSA authority, valid insurance at required levels, and acceptable safety ratings",
            "Nothing—if they're on the load board, they're automatically qualified",
            "Only that they have a truck available",
            "Just their phone number and company name"
        ],
        "correct_index": 0,
        "explanation": "Federal regulations require brokers to verify that carriers have proper authority, insurance, and acceptable safety ratings before tendering freight. This includes active FMCSA operating authority, valid commercial auto liability insurance at required levels ($750K minimum for most freight), and acceptable safety ratings. Using carriers without proper credentials exposes you to enormous liability."
    }
]

# Quiz questions for Module 2.6
MODULE_2_6_QUIZ = [
    {
        "id": "q2_6_1",
        "question": "Your customer pays net 30 terms, but the carrier expects payment in 7 days. You haven't received customer payment yet. What should you do?",
        "choices": [
            "Negotiate with the carrier to accept net 30 terms too",
            "Tell the carrier they have to wait for the customer to pay first",
            "Pay the carrier according to your agreed terms (net 7)—your obligation exists regardless of when customers pay you",
            "Wait to pay the carrier until after the customer pays you"
        ],
        "correct_index": 2,
        "explanation": "The timing mismatch between customer payments (net 30) and carrier expectations (net 7) is normal in freight brokerage. Your obligation to pay carriers exists independently of when customers pay you. Paying carriers according to agreed terms builds relationships—carriers who aren't paid on time will stop accepting your loads and warn others about you."
    }
]

# Quiz questions for Module 2.7
MODULE_2_7_QUIZ = [
    {
        "id": "q2_7_1",
        "question": "It's mid-September, and a customer asks why rates have increased 20% compared to last month. What's the most likely explanation?",
        "choices": [
            "Pre-holiday season tight capacity as retailers stock shelves for holiday shopping—more loads than available trucks drives rates up",
            "Summer is ending so rates always increase in fall",
            "Carriers are price gouging for no reason",
            "Your brokerage increased fees without telling you"
        ],
        "correct_index": 0,
        "explanation": "September through early November sees tight capacity as retailers stock shelves for holiday shopping. This seasonal pattern creates more loads than available trucks, allowing carriers to be selective and demand higher rates. Understanding these predictable patterns helps you price appropriately and educate customers about market conditions rather than seeming arbitrary."
    }
]

# Quiz questions for Module 2.8
MODULE_2_8_QUIZ = [
    {
        "id": "q2_8_1",
        "question": "A small customer says a large national brokerage like C.H. Robinson quoted them a lower rate. How should you respond?",
        "choices": [
            "Tell them large brokerages provide terrible service",
            "Give up—you can't compete with large brokerages",
            "Emphasize your personal service, faster response times, flexibility, and direct customer relationships—you're their personal logistics advisor",
            "Match their rate exactly even if it means no profit for you"
        ],
        "correct_index": 2,
        "explanation": "Large brokerages have advantages in buying power and technology, but often provide bureaucratic, slow, inconsistent service where customers feel like small fish in a big pond. Your competitive advantage is personal service, faster response times, flexibility, and direct relationships. Position yourself as the 'personal logistics advisor' rather than competing on price or scale."
    }
]

# Quiz questions for Module 2.9
MODULE_2_9_QUIZ = [
    {
        "id": "q2_9_1",
        "question": "You have a background working in food manufacturing. How might this influence your niche selection?",
        "choices": [
            "Keep it secret from customers so they think you're objective",
            "Only work with construction companies to diversify away from your background",
            "It's irrelevant—avoid food industry freight because you know it too well",
            "Specialize in food and beverage freight—your background provides instant credibility and understanding of temperature requirements, food safety regulations, and industry needs"
        ],
        "correct_index": 3,
        "explanation": "Previous work experience in an industry provides instant credibility and understanding. Your food manufacturing background gives you knowledge of temperature requirements, food safety regulations, food-grade trailer specifications, and industry terminology. This expertise commands premium pricing and helps you build relationships faster than generalist competitors."
    }
]

# Chapter 3 Quizzes
chapter3_quizzes = [
    {
        "id": "q3_1_1",
        "question": "A customer calls with an urgent operational issue while you're in the middle of a prospecting call with a promising new lead. What should you do?",
        "choices": [
            "Finish the prospecting call first since new business is the lifeblood of your operation",
            "Excuse yourself from the prospecting call, handle the customer's urgent issue immediately, then call the prospect back later",
            "Let the customer's call go to voicemail and follow up after the prospecting call",
            "Ask the customer to email you the details while you finish the sales call"
        ],
        "correct_index": 1,
        "explanation": "Active shipments and customer service always take priority over sales activities. Operational issues require immediate attention because failing to manage them properly damages relationships with both customers and carriers. You can reschedule prospecting calls, but you can't recover from service failures."
    },
    {
        "id": "q3_2_1",
        "question": "A prospect who ships 40 loads monthly tells you they'll only work with you if you match rates that are 25% below current market conditions. How should you respond?",
        "choices": [
            "Accept their terms to secure the high-volume account and hope to increase rates later",
            "This prospect isn't qualified—politely explain your rates reflect market conditions and move on to better prospects",
            "Agree to their rates but provide minimal service to protect your margins",
            "Counter-offer at 20% below market instead of 25%"
        ],
        "correct_index": 1,
        "explanation": "Qualifying means determining whether a prospect is genuinely worth pursuing. A company demanding rates 25% below market isn't qualified regardless of volume. Quality matters more than quantity. Working at unsustainable margins creates a cycle of working hard for minimal income and eventual business failure."
    },
    {
        "id": "q3_2_2",
        "question": "You're presenting your services to a logistics manager who mentions they're frustrated by poor communication from their current provider. What's the most effective approach?",
        "choices": [
            "Provide a generic overview of all your company's services and capabilities",
            "Immediately quote lower rates than their current provider",
            "Connect directly to their specific concern: 'Communication is critical. Here's exactly how I'll keep you updated proactively at every stage of the shipment—pickup confirmation, mid-transit updates, and delivery confirmation—so you never wonder where your freight is.'",
            "Tell them your brokerage has the best technology in the industry"
        ],
        "correct_index": 2,
        "explanation": "Effective presenting means connecting your services directly to the prospect's specific situation. When they mention poor communication as their pain point, address that concern specifically with concrete examples of how you'll solve that problem. Generic presentations about how great your company is rarely work."
    },
    {
        "id": "q3_3_1",
        "question": "A customer says they need to ship '25,000 lbs of parts from Dallas to Atlanta next Tuesday.' What's your next step?",
        "choices": [
            "Immediately post this on a load board to find available carriers",
            "Quote them a rate based on typical Dallas-Atlanta pricing",
            "Gather complete load details: specific pickup and delivery addresses, appointment times, exact commodity, dimensions, piece count, special requirements, and contact information",
            "Ask if they prefer dry van or flatbed equipment"
        ],
        "correct_index": 2,
        "explanation": "Every shipment requires specific information before you can price it accurately and find an appropriate carrier. General terms like 'parts' aren't sufficient. Missing or incorrect details cause problems later. Complete information gathering is the essential first step in load booking."
    },
    {
        "id": "q3_3_2",
        "question": "You book a load from a customer for $1,800. To preserve healthy margins, you want to pay the carrier no more than $1,300. Which factor should be LEAST important in determining if this carrier rate is realistic?",
        "choices": [
            "How much commission you personally want to earn",
            "Current market rates for this specific lane",
            "Difficulty factors like rural locations or tight appointment times",
            "Seasonal capacity conditions in the market"
        ],
        "correct_index": 0,
        "explanation": "While your desired margin matters, pricing should primarily reflect real market conditions and the difficulty of the shipment. Current market rates, lane difficulty, urgency, and capacity conditions should drive your carrier rate expectations. Unrealistic carrier rates based solely on what you want to earn won't attract quality carriers and will cause service failures."
    },
    {
        "id": "q3_4_1",
        "question": "You receive a call from a driver who says he'll be 45 minutes late to a delivery appointment due to an unexpected traffic delay. The customer's receiving hours close in one hour. What should you do first?",
        "choices": [
            "Tell the driver to do his best and hope he makes it on time",
            "Wait to see if the driver actually delivers late before contacting the customer",
            "Immediately call the customer, explain the situation, and ask if they can stay open an extra 30 minutes to accommodate the delay",
            "Document the delay in your TMS system for your records"
        ],
        "correct_index": 2,
        "explanation": "Proactive communication before problems become crises is essential. Contact the customer immediately to explain the situation and propose solutions. This gives them time to adjust their schedule and shows you're managing the situation attentively. Waiting until after a problem occurs damages trust and eliminates options for resolution."
    },
    {
        "id": "q3_4_2",
        "question": "Three months after delivery, a customer disputes a $150 detention charge on an invoice. They claim the driver wasn't delayed. What's your best course of action?",
        "choices": [
            "Immediately waive the charge to maintain the customer relationship",
            "Refuse to discuss it since three months have passed",
            "Gather all relevant documentation (BOL, POD, rate confirmation, detention documentation, timestamps) to understand what actually happened, then make a fair decision based on facts",
            "Tell the customer it's the carrier's fault, not yours"
        ],
        "correct_index": 2,
        "explanation": "Dispute resolution requires gathering all relevant documentation to determine what's fair based on facts. Sometimes the customer is right, sometimes the carrier is right, and sometimes both parties share responsibility. Make decisions based on documentation and facts, not on assumptions or expediency."
    },
    {
        "id": "q3_5_1",
        "question": "A carrier you've worked with successfully on five previous loads completes a delivery on Friday. Your payment terms with carriers are net 15 days. Your customer hasn't paid you yet and likely won't pay for 25 days. When should you pay the carrier?",
        "choices": [
            "Wait until you receive payment from the customer first",
            "Pay the carrier in 15 days as agreed, regardless of whether the customer has paid you",
            "Explain to the carrier that payment will be delayed until the customer pays",
            "Offer to pay in 30 days instead since that's more convenient for your cash flow"
        ],
        "correct_index": 1,
        "explanation": "Pay carriers according to agreed terms regardless of whether customers have paid you. Your obligation to carriers exists independently of whether you've been paid. Late payment damages relationships severely. Carriers who aren't paid on time will stop accepting your loads, and word spreads through the carrier community about agents who don't pay fairly or promptly."
    },
    {
        "id": "q3_5_2",
        "question": "You notice that a customer consistently provides good volume (12-15 loads monthly) but the margins average only 8% compared to your typical 18% margins. What should you consider before deciding whether to continue the relationship?",
        "choices": [
            "Immediately stop working with them since 8% margins are unacceptable",
            "Calculate relationship profitability, not just per-load margins—15 loads monthly at 8% might generate more total income than 3 loads monthly at 20%",
            "Reduce service quality to match the lower margins",
            "Focus only on the percentage margin since that's the key metric"
        ],
        "correct_index": 1,
        "explanation": "Don't make decisions based purely on individual load margins. Calculate relationship profitability, not just transaction profitability. A high-volume customer paying slightly lower margins might be more valuable than a customer paying high margins on infrequent shipments. Consider total income, relationship stability, and growth potential when evaluating customer relationships."
    },
    {
        "id": "q3_6_1",
        "question": "You've found a new carrier offering very competitive rates on a lane you frequently use. They have an active DOT number but you're having trouble verifying their insurance information. What should you do?",
        "choices": [
            "Use them for one test load to see how they perform, then verify insurance if they do well",
            "Do not tender freight to this carrier until you've verified they have valid commercial auto liability insurance at required levels—this is a legal requirement",
            "Ask the carrier to email you their insurance information and accept whatever they send",
            "Assume their insurance is valid since they have an active DOT number"
        ],
        "correct_index": 1,
        "explanation": "Federal regulations require brokers to verify that carriers have proper authority, insurance, and acceptable safety ratings before tendering freight. This isn't optional—it's a legal requirement that protects you from enormous liability. Using a carrier without verified proper insurance exposes you to serious financial and legal risk if accidents or cargo loss occurs."
    },
    {
        "id": "q3_6_2",
        "question": "It's Friday afternoon and you're completing paperwork for the week. You realize you haven't filed the proof of delivery for a shipment that delivered on Monday. When should you handle this?",
        "choices": [
            "It can wait until next week since it's already Friday afternoon",
            "File it immediately—organize documentation while details are fresh, and you may need these records for invoicing, disputes, or compliance purposes",
            "Only file important documents; routine PODs don't need to be saved",
            "Email it to someone else in your office to file for you"
        ],
        "correct_index": 1,
        "explanation": "Maintain organized records of all transactions and documents. Handle documentation while details are fresh, and ensure you can quickly locate any document related to any shipment. Three months later, when a customer questions a charge or you need to prove delivery, you must have immediate access to supporting documentation. Delayed or incomplete record keeping creates problems."
    },
    {
        "id": "q3_7_1",
        "question": "You notice that several carriers have mentioned capacity is getting tighter on your primary lanes over the past two weeks. What should you do with this information?",
        "choices": [
            "Keep it to yourself so competitors don't benefit from your intelligence",
            "Share this market intelligence proactively with your customers, helping them understand they may need to plan further ahead and expect slightly higher rates",
            "Wait until customers complain about rates before mentioning market conditions",
            "Immediately raise all your rates by 20%"
        ],
        "correct_index": 1,
        "explanation": "Market intelligence from carrier communication provides valuable insights. Sharing this intelligence proactively with customers demonstrates expertise and helps them make better decisions. This positions you as a trusted advisor providing value beyond just booking loads. Customers appreciate advance warning about market changes that might affect their operations."
    },
    {
        "id": "q3_7_2",
        "question": "You've been working as a freight agent for six months and notice you struggle with negotiating carrier rates effectively. How should you address this skill gap?",
        "choices": [
            "Avoid negotiating by always accepting carriers' first quoted rates",
            "Just keep doing what you're doing—you'll improve naturally over time",
            "Identify this as a skill needing development: read books on negotiation tactics, practice with lower-stakes loads, seek advice from experienced agents, and analyze what approaches work best",
            "Delegate all carrier negotiations to someone else at your brokerage"
        ],
        "correct_index": 2,
        "explanation": "Successful agents identify skills they need to improve and actively work on developing them. Continuous learning means recognizing weaknesses, studying techniques, practicing deliberately, and refining your approach based on results. Skill development requires intentional effort, not just hoping you'll improve over time."
    },
    {
        "id": "q3_8_1",
        "question": "It's 10:30 AM on a Tuesday. You have three active shipments tracking on time, no immediate issues, and your scheduled prospecting block starts at 11:00 AM. What should you do in the next 30 minutes?",
        "choices": [
            "Take a break since you're ahead of schedule",
            "Start prospecting calls 30 minutes early since active shipments are running smoothly",
            "Process administrative tasks like invoicing completed deliveries, updating documentation, or checking on upcoming shipment details",
            "Leave the office early since everything is under control"
        ],
        "correct_index": 2,
        "explanation": "When active shipments are running smoothly, use available time productively for administrative tasks or early prospecting. Batching administrative work—doing all invoicing at once, processing documentation together—improves efficiency. Don't waste productive time when you could be invoicing completed deliveries, organizing records, or handling other essential administrative tasks."
    },
    {
        "id": "q3_8_2",
        "question": "You're following up on a quote you provided yesterday when a current customer calls with an urgent issue about a delivery scheduled for today. How should you prioritize these two activities?",
        "choices": [
            "Finish the follow-up call since you already started it",
            "Immediately shift to the customer's urgent issue—active shipments always take priority over sales activities",
            "Ask the customer to hold while you finish the other call",
            "Split your attention between both calls simultaneously"
        ],
        "correct_index": 1,
        "explanation": "Active shipments and customer service always take priority. When a customer calls with an urgent issue, drop everything else and handle it immediately. You can make prospecting or follow-up calls later, but you can't recover from service failures. This prioritization builds trust and ensures operational excellence."
    },
    {
        "id": "q3_9_1",
        "question": "A driver got lost and delivered three hours late due to their GPS malfunction. The customer is upset and questioning whether they should continue using your services. How should you respond?",
        "choices": [
            "Explain it's the driver's fault, not yours, so the customer shouldn't hold it against you",
            "Blame the carrier company for giving you a bad driver",
            "Take complete ownership: 'I understand this was unacceptable. This is my load and my responsibility to fix. Here's what I'm doing to ensure it doesn't happen again, and here's how I'll make this right.'",
            "Suggest the customer should have provided better directions"
        ],
        "correct_index": 2,
        "explanation": "Take complete ownership of every shipment you book. When you accept a load, it becomes your load and you're accountable for its success regardless of what goes wrong or whose fault it might be. Customers don't care whose fault problems are—they care about results. Taking ownership builds reputation as someone who makes things happen rather than makes excuses."
    },
    {
        "id": "q3_9_2",
        "question": "A customer needs a shipment covered during extremely tight capacity. You'll need to pay carrier rates that leave you with a $50 margin instead of your typical $300 margin. The customer represents $15,000 in annual revenue. What's the best approach?",
        "choices": [
            "Decline the shipment since the margin doesn't meet your standards",
            "Tell the customer you can't help them during tight capacity periods",
            "Accept the smaller margin to preserve a valuable long-term relationship worth thousands in future revenue",
            "Lie about carrier rates being even higher so you can maintain your usual margin"
        ],
        "correct_index": 2,
        "explanation": "Prioritize long-term relationships over short-term profits. Sometimes earning a small margin (or even breaking even) maintains relationships worth thousands in future revenue. Long-term thinking focuses on building a business that generates substantial income for years, not just maximizing this quarter's commission. Customers remember agents who came through when capacity was tight."
    },
    {
        "id": "q3_9_3",
        "question": "You notice you've had three shipments this month where detention charges were disputed by customers. They all involved confusion about free time policies. What should you do?",
        "choices": [
            "Nothing—disputes are just part of the business",
            "Stop charging detention since it causes disputes",
            "Learn from the pattern: modify your process to communicate free time policies clearly upfront in rate confirmations and customer communications to prevent future disputes",
            "Blame customers for not understanding standard industry practices"
        ],
        "correct_index": 2,
        "explanation": "Continuous improvement means regularly reflecting on your performance and looking for ways to improve. When you notice patterns of disputes, identify the root cause and modify your processes to prevent future occurrences. Many disputes arise from preventable miscommunications. Learning from problems and adjusting your approach prevents repeating mistakes."
    }
]


def parse_project_outline(markdown_text: str):
    chapters_by_id = {}
    has_glossary = False
    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        m1 = re.match(r"^Chapter\s+(\d+):\s*(.+)$", line, flags=re.IGNORECASE)
        if m1:
            cid = int(m1.group(1))
            title = m1.group(2).strip()
            # Convert to title case if it's all uppercase
            if title.isupper():
                title = title.title()
            chapters_by_id[cid] = {"id": cid, "title": title}
            continue
        m2 = re.match(r"^CHAPTER\s+(\d+):\s*(.+)$", line, flags=re.IGNORECASE)
        if m2 and int(m2.group(1)) not in chapters_by_id:
            cid = int(m2.group(1))
            title = m2.group(2).strip()
            # Convert to title case if it's all uppercase
            if title.isupper():
                title = title.title()
            chapters_by_id[cid] = {"id": cid, "title": title}
        # Check for glossary
        if re.match(r"^GLOSSARY OF FREIGHT AGENT TERMS$", line, flags=re.IGNORECASE):
            has_glossary = True
    chapters = [chapters_by_id[k] for k in sorted(chapters_by_id.keys())]
    # Add glossary as a special entry after chapters
    if has_glossary:
        chapters.append({"id": "glossary", "title": "Glossary"})
    print(f"[parse_project_outline] Found {len(chapters)} chapters (including glossary: {has_glossary})")
    return chapters


def extract_chapter_content(markdown_text: str, chapter_id: int):
    # Match only uppercase CHAPTER headers (not TOC-style "Chapter")
    chapter_header_pattern = re.compile(rf"^CHAPTER\s+{chapter_id}:\s*(.+)$")
    next_chapter_header_pattern = re.compile(r"^CHAPTER\s+\d+:\s*")
    module_header_pattern = re.compile(r"^Module\s+(\d+\.\d+):\s*(.+)$")
    summary_header_pattern = re.compile(rf"^CHAPTER\s+{chapter_id}\s+SUMMARY.*$", re.IGNORECASE)
    action_items_header_pattern = re.compile(rf"^ACTION\s+ITEMS\s+FOR\s+CHAPTER\s+{chapter_id}\s*$", re.IGNORECASE)

    lines = markdown_text.splitlines()
    in_chapter = False
    chapter_title = None
    intro_lines = []
    modules = []
    current_module = None
    summary_lines = []
    in_summary = False
    action_items_lines = []
    in_action_items = False

    for raw_line in lines:
        stripped = raw_line.strip()
        enter = chapter_header_pattern.match(stripped)
        if not in_chapter and enter:
            in_chapter = True
            chapter_title = enter.group(1).strip()
            # Convert to title case if it's all uppercase
            if chapter_title.isupper():
                chapter_title = chapter_title.title()
            continue
        if not in_chapter:
            continue
        if next_chapter_header_pattern.match(stripped):
            break
        if summary_header_pattern.match(stripped):
            in_summary = True
            in_action_items = False
            if current_module:
                modules.append(current_module)
                current_module = None
            continue
        if action_items_header_pattern.match(stripped):
            in_action_items = True
            in_summary = False
            if current_module:
                modules.append(current_module)
                current_module = None
            continue
        m = module_header_pattern.match(stripped)
        if m and not in_summary and not in_action_items:
            if current_module:
                modules.append(current_module)
            current_module = {"id": m.group(1), "title": m.group(2).strip(), "content": []}
            continue
        if in_summary:
            summary_lines.append(raw_line)
        elif in_action_items:
            action_items_lines.append(raw_line)
        elif current_module is not None:
            current_module["content"].append(raw_line)
        else:
            if stripped != "":
                intro_lines.append(raw_line)
    if current_module:
        modules.append(current_module)

    print(
        f"[extract_chapter_content] ch={chapter_id} modules={len(modules)} "
        f"summary={'yes' if summary_lines else 'no'} action_items={'yes' if action_items_lines else 'no'}"
    )

    return {
        "chapter_id": chapter_id,
        "chapter_title": chapter_title or "",
        "intro": "\n".join(intro_lines).strip() if intro_lines else None,
        "modules": modules,
        "summary": "\n".join(summary_lines).strip() if summary_lines else None,
        "action_items": "\n".join(action_items_lines).strip() if action_items_lines else None,
    }


def preprocess_content(text: str) -> str:
    """Add markdown formatting to plain text content by detecting patterns."""
    if not text:
        return ""
    
    lines = text.split('\n')
    processed = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            processed.append('')
            continue
        
        # Detect section headers - short lines (< 50 chars) followed by content
        # Common patterns: "Time Savings", "Risk Management", "Months 1-3: The Learning Phase"
        is_section_header = False
        if len(stripped) < 70 and i < len(lines) - 1:
            next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
            # If this line is short and next line is substantial content (not another header)
            if next_line and len(next_line) > 50:
                # Check if it looks like a header (title case, ends with colon, or short phrase)
                if (stripped[0].isupper() and 
                    (stripped.endswith(':') or 
                     stripped.count(' ') <= 5 or
                     any(stripped.startswith(prefix) for prefix in ['Months ', 'Year ', 'Why ', 'What ', 'The ']))):
                    is_section_header = True
        
        if is_section_header:
            # Add blank line before header for spacing and make it bold
            if processed and processed[-1] != '':
                processed.append('')
            processed.append(f"**{stripped}**")
            processed.append('')
        else:
            processed.append(line)
    
    return '\n'.join(processed)


def process_callouts(text: str) -> str:
    """Convert callout syntax [TYPE] content to HTML with special styling."""
    if not text:
        return ""
    
    # Pattern: [TYPE] Content (on its own line or paragraph)
    callout_pattern = re.compile(r'\[([A-Z\s]+)\]\s*(.+?)(?=\n\n|\[(?:[A-Z\s]+)\]|$)', re.DOTALL)
    
    def replace_callout(match):
        callout_type = match.group(1).strip()
        content = match.group(2).strip()
        
        # Map types to styles and icons
        styles = {
            'PRO TIP': ('callout-tip', '💡'),
            'COMMON MISTAKE': ('callout-warning', '⚠️'),
            'REAL EXAMPLE': ('callout-example', '📊'),
            'KEY TAKEAWAY': ('callout-key', '🎯'),
            'IMPORTANT': ('callout-important', '⚡'),
            'NOTE': ('callout-note', '📝')
        }
        
        css_class, icon = styles.get(callout_type, ('callout-default', '📌'))
        
        return f'<div class="callout {css_class}"><div class="callout-title">{icon} <strong>{callout_type}</strong></div><div class="callout-content">{content}</div></div>\n\n'
    
    return callout_pattern.sub(replace_callout, text)


def convert_to_html(text: str) -> str:
    """Convert markdown text to HTML, preserving formatting."""
    if not text:
        return ""
    
    # Process callouts first (before markdown conversion)
    text_with_callouts = process_callouts(text)
    
    # Preprocess to add markdown formatting
    formatted_text = preprocess_content(text_with_callouts)
    
    # Convert markdown to HTML with extensions for better formatting
    md = markdown.Markdown(extensions=['nl2br', 'sane_lists'])
    return md.convert(formatted_text)


def estimate_visual_height(line: str, is_in_callout: bool = False, is_callout_start: bool = False) -> float:
    """
    Estimate the visual height cost of a line of text.
    Returns a "height score" where 1.0 = one line of regular text.
    
    Callouts are much taller due to borders, padding, and styling.
    """
    stripped = line.strip()
    
    # Empty lines
    if not stripped:
        return 0.5 if not is_in_callout else 0.3
    
    # Callout start line - includes title bar with icon + padding
    if is_callout_start:
        return 4.0  # Title + top padding + borders
    
    # Content inside callout - extra padding and line spacing
    if is_in_callout:
        char_count = len(stripped)
        # Callouts have padding and styled boxes, so they're taller
        lines_of_text = max(1, char_count / 50)  # ~50 chars per line in callouts
        return lines_of_text * 1.8  # 1.8x taller due to padding
    
    # Bold headers
    if stripped.startswith('**') and stripped.endswith('**'):
        return 2.5  # Headers are larger and have spacing
    
    # Regular text - estimate lines based on character count
    char_count = len(stripped)
    if char_count == 0:
        return 0.5
    
    # Assume ~60 chars per line for regular text
    lines_of_text = max(1, char_count / 60)
    return lines_of_text * 1.2  # Account for line height


def split_content_into_pages(content_text: str, max_height_score: float = 35.0) -> list:
    """
    Split long content into multiple pages based on estimated VISUAL HEIGHT.
    
    Instead of counting characters, we estimate how tall content will render:
    - Regular text: ~1.0-1.2 height units per line
    - Bold headers: ~2.5 height units (larger font + spacing)
    - Callout boxes: ~4.0 for title + 1.8x per line of content (padding + borders)
    
    Max height score of 35.0 = approximately viewport height without scrolling.
    Never splits callout blocks ([TYPE] content).
    """
    if not content_text:
        return [content_text]
    
    # Split by lines first
    lines = content_text.split('\n')
    pages = []
    current_page = []
    current_height = 0.0
    in_callout = False
    callout_lines = []
    callout_pattern = re.compile(r'^\[([A-Z\s]+)\]')
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Detect callout start
        is_callout_start = callout_pattern.match(stripped) is not None
        if is_callout_start:
            in_callout = True
            callout_lines = [line]
            continue  # Don't add yet, collect whole callout first
        
        # If in callout, collect lines
        if in_callout:
            callout_lines.append(line)
            # Detect callout end (empty line after content)
            if stripped == '' and len(callout_lines) > 1:
                # Callout is complete, calculate its total height
                callout_height = estimate_visual_height(callout_lines[0], False, True)  # Title
                for callout_line in callout_lines[1:]:
                    callout_height += estimate_visual_height(callout_line, True, False)
                
                # If adding callout would exceed limit, start new page
                if current_height + callout_height > max_height_score and current_page:
                    pages.append('\n'.join(current_page))
                    current_page = callout_lines.copy()
                    current_height = callout_height
                else:
                    current_page.extend(callout_lines)
                    current_height += callout_height
                
                in_callout = False
                callout_lines = []
            continue
        
        # Regular line (not in callout)
        line_height = estimate_visual_height(line, False, False)
        
        # If adding this line would exceed limit, start new page
        if current_height + line_height > max_height_score and current_page:
            # If current line is a header, include it in next page
            if stripped.startswith('**'):
                pages.append('\n'.join(current_page))
                current_page = [line]
                current_height = line_height
            else:
                current_page.append(line)
                pages.append('\n'.join(current_page))
                current_page = []
                current_height = 0.0
        else:
            current_page.append(line)
            current_height += line_height
    
    # Add any remaining callout lines if still in callout (shouldn't happen but safety)
    if callout_lines:
        current_page.extend(callout_lines)
    
    # Add the last page
    if current_page:
        pages.append('\n'.join(current_page))
    
    return pages


def extract_glossary(markdown_text: str):
    """Extract glossary terms from the markdown."""
    lines = markdown_text.splitlines()
    in_glossary = False
    glossary_lines = []
    
    for raw_line in lines:
        stripped = raw_line.strip()
        if re.match(r"^GLOSSARY OF FREIGHT AGENT TERMS$", stripped, flags=re.IGNORECASE):
            in_glossary = True
            continue
        if in_glossary and stripped:
            glossary_lines.append(raw_line)
    
    print(f"[extract_glossary] Found {len(glossary_lines)} glossary terms")
    return "\n".join(glossary_lines).strip()


def parse_glossary_terms(markdown_text: str):
    """Parse glossary into structured term objects."""
    glossary_text = extract_glossary(markdown_text)
    terms = []
    
    # Pattern: "Mod X.X - Term Name - Definition"
    pattern = re.compile(r'^(Mod\s+[\d.]+)\s*-\s*([^-]+?)\s*-\s*(.+)$')
    
    for line in glossary_text.splitlines():
        line = line.strip()
        if not line:
            continue
        match = pattern.match(line)
        if match:
            terms.append({
                'module': match.group(1).strip(),
                'name': match.group(2).strip(),
                'definition': match.group(3).strip()
            })
    
    print(f"[parse_glossary_terms] Parsed {len(terms)} structured terms")
    return terms


def get_module_completion_status(session_quiz_answers, module_id):
    """Check if all quizzes for a module are completed."""
    quiz_map = {
        "1.1": MODULE_1_1_QUIZ,
        "1.2": MODULE_1_2_QUIZ,
        "1.3": MODULE_1_3_QUIZ,
        "1.4": MODULE_1_4_QUIZ,
        "1.5": MODULE_1_5_QUIZ,
        "1.6": MODULE_1_6_QUIZ,
        "2.1": MODULE_2_1_QUIZ,
        "2.2": MODULE_2_2_QUIZ,
        "2.3": MODULE_2_3_QUIZ,
        "2.4": MODULE_2_4_QUIZ,
        "2.5": MODULE_2_5_QUIZ,
        "2.6": MODULE_2_6_QUIZ,
        "2.7": MODULE_2_7_QUIZ,
        "2.8": MODULE_2_8_QUIZ,
        "2.9": MODULE_2_9_QUIZ,
        "3.1": [q for q in chapter3_quizzes if q["id"].startswith("q3_1")],
        "3.2": [q for q in chapter3_quizzes if q["id"].startswith("q3_2")],
        "3.3": [q for q in chapter3_quizzes if q["id"].startswith("q3_3")],
        "3.4": [q for q in chapter3_quizzes if q["id"].startswith("q3_4")],
        "3.5": [q for q in chapter3_quizzes if q["id"].startswith("q3_5")],
        "3.6": [q for q in chapter3_quizzes if q["id"].startswith("q3_6")],
        "3.7": [q for q in chapter3_quizzes if q["id"].startswith("q3_7")],
        "3.8": [q for q in chapter3_quizzes if q["id"].startswith("q3_8")],
        "3.9": [q for q in chapter3_quizzes if q["id"].startswith("q3_9")],
    }
    
    if module_id not in quiz_map:
        return True  # Modules without quizzes are considered complete
    
    quiz_questions = quiz_map[module_id]
    for question in quiz_questions:
        if not session_quiz_answers.get(question["id"], False):
            return False
    return True


def get_chapter_completion_status(session_quiz_answers, chapter_num):
    """Check if all modules in a chapter are completed."""
    chapter_modules = {
        1: ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6"],
        2: ["2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8", "2.9"],
        3: ["3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "3.8", "3.9"],
    }
    
    if chapter_num not in chapter_modules:
        return True
    
    module_ids = chapter_modules[chapter_num]
    for mod_id in module_ids:
        if not get_module_completion_status(session_quiz_answers, mod_id):
            return False
    return True


def get_all_modules_completed(session_quiz_answers):
    """Check if all Chapter 1 modules are completed."""
    return get_chapter_completion_status(session_quiz_answers, 1)


def build_pages(text: str):
    """Build a flat list of pages: Cover, TOC, then all chapters with modules, summaries, action items."""
    chapters = parse_project_outline(text)
    ch1 = extract_chapter_content(text, 1)
    ch2 = extract_chapter_content(text, 2)
    ch3 = extract_chapter_content(text, 3)
    
    pages = []
    module_page_map = {}  # Maps module_id -> page_num
    quiz_page_map = {}  # Maps quiz_id -> page_num
    
    # Page 0: Cover page (lines 1-27 of project.md)
    lines = text.splitlines()
    cover_content = "\n".join(lines[0:27]) if len(lines) >= 27 else ""
    pages.append({"type": "cover", "content": cover_content, "ch1_modules": ch1["modules"], "ch2_modules": ch2["modules"], "ch3_modules": ch3["modules"]})
    
    # Page 1: Table of Contents
    pages.append({"type": "toc", "chapters": chapters, "ch1_modules": ch1["modules"], "ch2_modules": ch2["modules"], "ch3_modules": ch3["modules"]})
    
    # Chapter 1 intro
    if ch1["intro"]:
        pages.append({
            "type": "intro",
            "chapter_id": 1,
            "chapter_title": ch1["chapter_title"],
            "content": ch1["intro"],
            "content_html": convert_to_html(ch1["intro"])
        })
    
    # Chapter 1 modules
    for mod in ch1["modules"]:
        module_page_map[mod["id"]] = len(pages)  # Record the first page number for this module
        content_text = "\n".join(mod["content"])
        
        # Split module content into multiple pages if needed
        content_pages = split_content_into_pages(content_text)
        
        for page_idx, page_content in enumerate(content_pages):
            pages.append({
                "type": "module",
                "chapter_id": 1,
                "chapter_title": ch1["chapter_title"],
                "module_id": mod["id"],
                "module_title": mod["title"],
                "content": page_content,
                "content_html": convert_to_html(page_content),
                "module_page_num": page_idx + 1,
                "module_total_pages": len(content_pages)
            })
        
        # Add quiz questions after the last page of each module
        quiz_map = {
            "1.1": MODULE_1_1_QUIZ,
            "1.2": MODULE_1_2_QUIZ,
            "1.3": MODULE_1_3_QUIZ,
            "1.4": MODULE_1_4_QUIZ,
            "1.5": MODULE_1_5_QUIZ,
            "1.6": MODULE_1_6_QUIZ,
        }
        
        if mod["id"] in quiz_map:
            quiz_questions = quiz_map[mod["id"]]
            for idx, quiz_question in enumerate(quiz_questions):
                quiz_page_map[quiz_question["id"]] = len(pages)  # Track quiz question page number
                pages.append({
                    "type": "quiz",
                    "chapter_id": 1,
                    "module_id": mod["id"],
                    "module_title": mod["title"],
                    "quiz_question": quiz_question,
                    "question_number": idx + 1,
                    "total_questions": len(quiz_questions)
                })
    
    # Chapter 1 summary
    if ch1["summary"]:
        pages.append({
            "type": "summary",
            "chapter_id": 1,
            "chapter_title": ch1["chapter_title"],
            "content": ch1["summary"],
            "content_html": convert_to_html(ch1["summary"])
        })
    
    # Chapter 1 action items
    if ch1["action_items"]:
        pages.append({
            "type": "action_items",
            "chapter_id": 1,
            "chapter_title": ch1["chapter_title"],
            "content": ch1["action_items"],
            "content_html": convert_to_html(ch1["action_items"])
        })
    
    # Chapter 2 intro
    if ch2["intro"]:
        pages.append({
            "type": "intro",
            "chapter_id": 2,
            "chapter_title": ch2["chapter_title"],
            "content": ch2["intro"],
            "content_html": convert_to_html(ch2["intro"])
        })
    
    # Chapter 2 modules
    for mod in ch2["modules"]:
        module_page_map[mod["id"]] = len(pages)  # Record the first page number for this module
        content_text = "\n".join(mod["content"])
        
        # Split module content into multiple pages if needed
        content_pages = split_content_into_pages(content_text)
        
        for page_idx, page_content in enumerate(content_pages):
            pages.append({
                "type": "module",
                "chapter_id": 2,
                "chapter_title": ch2["chapter_title"],
                "module_id": mod["id"],
                "module_title": mod["title"],
                "content": page_content,
                "content_html": convert_to_html(page_content),
                "module_page_num": page_idx + 1,
                "module_total_pages": len(content_pages)
            })
        
        # Add quiz questions after the last page of each module
        quiz_map_ch2 = {
            "2.1": MODULE_2_1_QUIZ,
            "2.2": MODULE_2_2_QUIZ,
            "2.3": MODULE_2_3_QUIZ,
            "2.4": MODULE_2_4_QUIZ,
            "2.5": MODULE_2_5_QUIZ,
            "2.6": MODULE_2_6_QUIZ,
            "2.7": MODULE_2_7_QUIZ,
            "2.8": MODULE_2_8_QUIZ,
            "2.9": MODULE_2_9_QUIZ,
        }
        
        if mod["id"] in quiz_map_ch2:
            quiz_questions = quiz_map_ch2[mod["id"]]
            for idx, quiz_question in enumerate(quiz_questions):
                quiz_page_map[quiz_question["id"]] = len(pages)  # Track quiz question page number
                pages.append({
                    "type": "quiz",
                    "chapter_id": 2,
                    "module_id": mod["id"],
                    "module_title": mod["title"],
                    "quiz_question": quiz_question,
                    "question_number": idx + 1,
                    "total_questions": len(quiz_questions)
                })
    
    # Chapter 2 summary
    if ch2["summary"]:
        pages.append({
            "type": "summary",
            "chapter_id": 2,
            "chapter_title": ch2["chapter_title"],
            "content": ch2["summary"],
            "content_html": convert_to_html(ch2["summary"])
        })
    
    # Chapter 2 action items
    if ch2["action_items"]:
        pages.append({
            "type": "action_items",
            "chapter_id": 2,
            "chapter_title": ch2["chapter_title"],
            "content": ch2["action_items"],
            "content_html": convert_to_html(ch2["action_items"])
        })
    
    # Chapter 3 intro
    if ch3["intro"]:
        pages.append({
            "type": "intro",
            "chapter_id": 3,
            "chapter_title": ch3["chapter_title"],
            "content": ch3["intro"],
            "content_html": convert_to_html(ch3["intro"])
        })
    
    # Chapter 3 modules
    for mod in ch3["modules"]:
        module_page_map[mod["id"]] = len(pages)  # Record the first page number for this module
        content_text = "\n".join(mod["content"])
        
        # Split module content into multiple pages if needed
        content_pages = split_content_into_pages(content_text)
        
        for page_idx, page_content in enumerate(content_pages):
            pages.append({
                "type": "module",
                "chapter_id": 3,
                "chapter_title": ch3["chapter_title"],
                "module_id": mod["id"],
                "module_title": mod["title"],
                "content": page_content,
                "content_html": convert_to_html(page_content),
                "module_page_num": page_idx + 1,
                "module_total_pages": len(content_pages)
            })
        
        # Add quiz questions after the last page of each module
        quiz_map_ch3 = {
            "3.1": [q for q in chapter3_quizzes if q["id"].startswith("q3_1")],
            "3.2": [q for q in chapter3_quizzes if q["id"].startswith("q3_2")],
            "3.3": [q for q in chapter3_quizzes if q["id"].startswith("q3_3")],
            "3.4": [q for q in chapter3_quizzes if q["id"].startswith("q3_4")],
            "3.5": [q for q in chapter3_quizzes if q["id"].startswith("q3_5")],
            "3.6": [q for q in chapter3_quizzes if q["id"].startswith("q3_6")],
            "3.7": [q for q in chapter3_quizzes if q["id"].startswith("q3_7")],
            "3.8": [q for q in chapter3_quizzes if q["id"].startswith("q3_8")],
            "3.9": [q for q in chapter3_quizzes if q["id"].startswith("q3_9")],
        }
        
        if mod["id"] in quiz_map_ch3:
            quiz_questions = quiz_map_ch3[mod["id"]]
            for idx, quiz_question in enumerate(quiz_questions):
                quiz_page_map[quiz_question["id"]] = len(pages)  # Track quiz question page number
                pages.append({
                    "type": "quiz",
                    "chapter_id": 3,
                    "module_id": mod["id"],
                    "module_title": mod["title"],
                    "quiz_question": quiz_question,
                    "question_number": idx + 1,
                    "total_questions": len(quiz_questions)
                })
    
    # Chapter 3 summary
    if ch3["summary"]:
        pages.append({
            "type": "summary",
            "chapter_id": 3,
            "chapter_title": ch3["chapter_title"],
            "content": ch3["summary"],
            "content_html": convert_to_html(ch3["summary"])
        })
    
    # Chapter 3 action items
    if ch3["action_items"]:
        pages.append({
            "type": "action_items",
            "chapter_id": 3,
            "chapter_title": ch3["chapter_title"],
            "content": ch3["action_items"],
            "content_html": convert_to_html(ch3["action_items"])
        })
    
    # Add module_page_map and quiz_page_map to cover and TOC pages
    pages[0]["module_page_map"] = module_page_map
    pages[0]["quiz_page_map"] = quiz_page_map
    pages[1]["module_page_map"] = module_page_map
    pages[1]["quiz_page_map"] = quiz_page_map
    
    # Note: Glossary is now a separate page at /glossary, not part of page navigation
    
    print(f"[build_pages] Built {len(pages)} pages")
    return pages


@app.route("/")
def index():
    return redirect(url_for("page", page_num=0))


@app.route("/page/<int:page_num>", methods=["GET", "POST"])
def page(page_num: int):
    try:
        text = PROJECT_MD_PATH.read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        text = ""
    
    pages = build_pages(text) if text else []
    
    if page_num < 0 or page_num >= len(pages):
        page_num = 0
    
    current_page = pages[page_num] if pages else {"type": "error", "content": "No content found"}
    
    # Initialize session for quiz answers if not exists
    if 'quiz_answers' not in session:
        session['quiz_answers'] = {}
    
    # Handle quiz answer submission
    quiz_feedback = None
    if request.method == "POST" and current_page.get("type") == "quiz":
        selected_answer = request.form.get("answer")
        if selected_answer is not None:
            selected_index = int(selected_answer)
            quiz_question = current_page["quiz_question"]
            correct_index = quiz_question["correct_index"]
            
            if selected_index == correct_index:
                # Correct answer - mark as answered and allow progression
                session['quiz_answers'][quiz_question["id"]] = True
                session.modified = True
                quiz_feedback = {
                    "correct": True,
                    "message": "Correct! " + quiz_question["explanation"]
                }
            else:
                # Incorrect answer
                quiz_feedback = {
                    "correct": False,
                    "message": "That's not quite right. Please try again.",
                    "selected_index": selected_index
                }
    
    # Check if current quiz question has been answered correctly
    quiz_answered = False
    if current_page.get("type") == "quiz":
        quiz_id = current_page["quiz_question"]["id"]
        quiz_answered = session['quiz_answers'].get(quiz_id, False)
    
    prev_num = page_num - 1 if page_num > 0 else None
    
    # Check if in preview mode (bypasses all locks for content creators)
    preview_mode = session.get('preview_mode', False)
    
    # Only allow next if not a quiz OR quiz has been answered correctly (or in preview mode)
    next_allowed = True
    if current_page.get("type") == "quiz" and not quiz_answered and not preview_mode:
        next_allowed = False
    
    # Check if trying to access a locked page (module/summary/action_items)
    if not preview_mode and current_page.get("type") == "module":
        # Check if previous modules are complete
        current_module_id = current_page.get("module_id")
        if current_module_id:
            # Define module sequences for each chapter
            chapter_1_modules = ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6"]
            chapter_2_modules = ["2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8", "2.9"]
            
            # Determine which chapter and check previous modules
            if current_module_id.startswith("1."):
                module_index = chapter_1_modules.index(current_module_id) if current_module_id in chapter_1_modules else 0
                if module_index > 0:
                    for i in range(module_index):
                        if not get_module_completion_status(session.get('quiz_answers', {}), chapter_1_modules[i]):
                            return redirect(url_for("page", page_num=1))
            elif current_module_id.startswith("2."):
                # For Chapter 2, first check if all Chapter 1 is complete
                if not get_chapter_completion_status(session.get('quiz_answers', {}), 1):
                    return redirect(url_for("page", page_num=1))
                # Then check previous Chapter 2 modules
                module_index = chapter_2_modules.index(current_module_id) if current_module_id in chapter_2_modules else 0
                if module_index > 0:
                    for i in range(module_index):
                        if not get_module_completion_status(session.get('quiz_answers', {}), chapter_2_modules[i]):
                            return redirect(url_for("page", page_num=1))
    
    # Lock summary and action items until all modules complete (unless in preview mode)
    if not preview_mode and current_page.get("type") in ["summary", "action_items"]:
        chapter_id = current_page.get("chapter_id", 1)
        if not get_chapter_completion_status(session.get('quiz_answers', {}), chapter_id):
            # Redirect to TOC if trying to access locked summary/action items
            return redirect(url_for("page", page_num=1))
    
    next_num = page_num + 1 if page_num < len(pages) - 1 and next_allowed else None
    
    # Get module-specific page counter from page data (resets per module)
    module_page_num = None
    module_total_pages = None
    
    if current_page.get("type") == "module":
        # Multi-page module support
        module_page_num = current_page.get("module_page_num", 1)
        module_total_pages = current_page.get("module_total_pages", 1)
    elif current_page.get("type") in ["intro", "summary", "action_items"]:
        # Single-page sections
        module_page_num = 1
        module_total_pages = 1
    
    # Check module completion status
    module_completion = {}
    all_ch1_modules_complete = False
    all_ch2_modules_complete = False
    all_ch3_modules_complete = False
    if pages:
        # Get modules from all chapters' data stored in pages
        ch1_modules = pages[0].get("ch1_modules", [])
        ch2_modules = pages[0].get("ch2_modules", [])
        ch3_modules = pages[0].get("ch3_modules", [])
        
        for mod in ch1_modules:
            module_completion[mod["id"]] = get_module_completion_status(session.get('quiz_answers', {}), mod["id"])
        all_ch1_modules_complete = get_chapter_completion_status(session.get('quiz_answers', {}), 1)
        
        for mod in ch2_modules:
            module_completion[mod["id"]] = get_module_completion_status(session.get('quiz_answers', {}), mod["id"])
        all_ch2_modules_complete = get_chapter_completion_status(session.get('quiz_answers', {}), 2)
        
        for mod in ch3_modules:
            module_completion[mod["id"]] = get_module_completion_status(session.get('quiz_answers', {}), mod["id"])
        all_ch3_modules_complete = get_chapter_completion_status(session.get('quiz_answers', {}), 3)
    
    # Quiz map for TOC dropdown display
    quiz_map = {
        "1.1": MODULE_1_1_QUIZ,
        "1.2": MODULE_1_2_QUIZ,
        "1.3": MODULE_1_3_QUIZ,
        "1.4": MODULE_1_4_QUIZ,
        "1.5": MODULE_1_5_QUIZ,
        "1.6": MODULE_1_6_QUIZ,
        "2.1": MODULE_2_1_QUIZ,
        "2.2": MODULE_2_2_QUIZ,
        "2.3": MODULE_2_3_QUIZ,
        "2.4": MODULE_2_4_QUIZ,
        "2.5": MODULE_2_5_QUIZ,
        "2.6": MODULE_2_6_QUIZ,
        "2.7": MODULE_2_7_QUIZ,
        "2.8": MODULE_2_8_QUIZ,
        "2.9": MODULE_2_9_QUIZ,
        "3.1": [q for q in chapter3_quizzes if q["id"].startswith("q3_1")],
        "3.2": [q for q in chapter3_quizzes if q["id"].startswith("q3_2")],
        "3.3": [q for q in chapter3_quizzes if q["id"].startswith("q3_3")],
        "3.4": [q for q in chapter3_quizzes if q["id"].startswith("q3_4")],
        "3.5": [q for q in chapter3_quizzes if q["id"].startswith("q3_5")],
        "3.6": [q for q in chapter3_quizzes if q["id"].startswith("q3_6")],
        "3.7": [q for q in chapter3_quizzes if q["id"].startswith("q3_7")],
        "3.8": [q for q in chapter3_quizzes if q["id"].startswith("q3_8")],
        "3.9": [q for q in chapter3_quizzes if q["id"].startswith("q3_9")],
    }
    
    return render_template(
        "page.html",
        page=current_page,
        page_num=page_num,
        total_pages=len(pages),
        prev_num=prev_num,
        next_num=next_num,
        quiz_feedback=quiz_feedback,
        quiz_answered=quiz_answered,
        module_page_num=module_page_num,
        module_total_pages=module_total_pages,
        module_completion=module_completion,
        all_ch1_modules_complete=all_ch1_modules_complete,
        all_ch2_modules_complete=all_ch2_modules_complete,
        all_ch3_modules_complete=all_ch3_modules_complete,
        preview_mode=preview_mode,
        quiz_map=quiz_map,
        quiz_answers=session.get('quiz_answers', {})
    )


@app.route("/glossary")
def glossary():
    try:
        text = PROJECT_MD_PATH.read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        text = ""
    
    glossary_terms = parse_glossary_terms(text) if text else []
    
    return render_template(
        "glossary.html",
        glossary_terms=glossary_terms
    )


@app.route("/reset")
def reset():
    """Reset all quiz progress and redirect to home."""
    session.clear()
    return redirect(url_for("page", page_num=0))


@app.route("/preview")
def preview():
    """Enable preview mode - unlocks all content for creators to review."""
    session['preview_mode'] = True
    return redirect(url_for("page", page_num=1))


if __name__ == "__main__":
    app.run(debug=True)
