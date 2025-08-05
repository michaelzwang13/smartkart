const { useState, useEffect } = React;

// Navigation Component
const Navigation = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const navLinks = [
    { name: "Features", href: "#features" },
    { name: "How it works", href: "#how-it-works" },
    { name: "Pricing", href: "#pricing" },
    { name: "Testimonials", href: "#testimonials" }
  ];

  return React.createElement('nav', { className: 'navigation' },
    React.createElement('div', { className: 'container' },
      React.createElement('div', { className: 'nav-container' },
        // Logo
        React.createElement('div', { className: 'logo' },
          React.createElement('div', { className: 'logo-icon' }, 'P'),
          React.createElement('span', { className: 'logo-text' }, 'Preppr')
        ),
        
        // Desktop navigation
        React.createElement('div', { className: 'nav-links desktop' },
          ...navLinks.map(link =>
            React.createElement('a', {
              key: link.name,
              href: link.href,
              className: 'nav-link'
            }, link.name)
          )
        ),
        
        // Desktop buttons
        React.createElement('div', { className: 'nav-buttons desktop' },
          React.createElement('a', { href: '/login', className: 'btn btn-ghost' }, 'Sign in'),
          React.createElement('a', { href: '/register', className: 'btn btn-primary' }, 'Get started free')
        ),
        
        // Mobile menu button
        React.createElement('button', {
          className: 'mobile-menu-button',
          onClick: () => setIsMenuOpen(!isMenuOpen)
        },
          React.createElement('span', { 
            className: isMenuOpen ? 'icon icon-x' : 'icon icon-menu' 
          })
        )
      ),
      
      // Mobile menu
      isMenuOpen && React.createElement('div', { className: 'mobile-menu open' },
        React.createElement('div', null,
          ...navLinks.map(link =>
            React.createElement('a', {
              key: link.name,
              href: link.href,
              className: 'nav-link',
              onClick: () => setIsMenuOpen(false)
            }, link.name)
          ),
          React.createElement('div', { className: 'mobile-menu-buttons' },
            React.createElement('a', { href: '/login', className: 'btn btn-ghost' }, 'Sign in'),
            React.createElement('a', { href: '/register', className: 'btn btn-primary' }, 'Get started free')
          )
        )
      )
    )
  );
};

// Hero Section Component
const HeroSection = () => {
  return React.createElement('section', { className: 'hero-section' },
    React.createElement('div', { className: 'hero-bg-decorations' }),
    React.createElement('div', { className: 'container' },
      React.createElement('div', { className: 'hero-grid' },
        // Left content
        React.createElement('div', { className: 'hero-content' },
          React.createElement('div', { className: 'hero-badge' },
            'Now in beta • Free to use'
          ),
          React.createElement('h1', { className: 'hero-title' },
            'Prep ',
            React.createElement('span', { className: 'gradient-text' }, 'smarter'),
            '. ',
            React.createElement('br'),
            'Save time. ',
            React.createElement('br'),
            React.createElement('span', { className: 'text-slate-medium' }, 'Eat better.')
          ),
          React.createElement('p', { className: 'hero-description' },
            'Your AI-powered meal planning companion that tracks your pantry, creates personalized meal plans, and optimizes your shopping—all while reducing food waste and fitting your budget.'
          ),
          React.createElement('div', { className: 'hero-buttons' },
            React.createElement('a', { href: '/register', className: 'btn btn-primary btn-hero' },
              'Start planning for free',
              React.createElement('span', { className: 'icon icon-arrow-right' })
            )
          ),
          React.createElement('div', { className: 'hero-features' },
            React.createElement('div', { className: 'hero-feature' },
              'No credit card required'
            ),
            React.createElement('div', { className: 'hero-feature' },
              'Free forever plan'
            )
          )
        ),
        
        // Right content - Hero image
        React.createElement('div', { className: 'hero-image-container' },
          React.createElement('div', { className: 'hero-image' },
            React.createElement('img', {
              src: '/static/images/meal-prep.jpg',
              alt: 'Meals prepped in containers'
            })
          ),
          
          // Floating stats cards
          React.createElement('div', { className: 'hero-stats top-left' },
            React.createElement('div', { className: 'stat-item' },
              React.createElement('div', { className: 'stat-dot emerald' }),
              React.createElement('div', null,
                React.createElement('div', { className: 'stat-value' }, '15 meals planned'),
                React.createElement('div', { className: 'stat-label' }, 'This week')
              )
            )
          ),
          
          React.createElement('div', { className: 'hero-stats bottom-right' },
            React.createElement('div', { className: 'stat-item' },
              React.createElement('div', { className: 'stat-dot accent' }),
              React.createElement('div', null,
                React.createElement('div', { className: 'stat-value' }, '$127 saved'),
                React.createElement('div', { className: 'stat-label' }, 'This month')
              )
            )
          )
        )
      )
    )
  );
};

// How It Works Section Component
const HowItWorksSection = () => {
  const steps = [
    {
      icon: 'icon-package',
      title: "Track your pantry",
      description: "Quickly scan or add items to your digital pantry. We'll track expiration dates and quantities automatically.",
      color: "text-emerald-dark"
    },
    {
      icon: 'icon-brain',
      title: "Get AI meal plans",
      description: "Our smart AI creates personalized meal plans based on your preferences, dietary needs, and what you already have.",
      color: "text-accent"
    },
    {
      icon: 'icon-shopping-cart',
      title: "Shop smarter",
      description: "Get optimized shopping lists organized by store layout and budget. Never overbuy or forget ingredients again.",
      color: "text-primary"
    }
  ];

  return React.createElement('section', { className: 'section', id: 'how-it-works' },
    React.createElement('div', { className: 'container' },
      React.createElement('div', { className: 'section-header' },
        React.createElement('h2', { className: 'section-title' },
          'How Preppr ',
          React.createElement('span', { className: 'gradient-text' }, 'simplifies'),
          ' your meal planning'
        ),
        React.createElement('p', { className: 'section-description' },
          'Three simple steps to transform your kitchen chaos into organized, budget-friendly meal planning.'
        )
      ),

      React.createElement('div', { className: 'how-it-works-grid' },
        // Workflow illustration
        React.createElement('div', { className: 'workflow-image' },
          React.createElement('img', {
            src: '../src/assets/workflow-illustration.jpg',
            alt: 'Preppr workflow illustration showing pantry tracking, AI planning, and smart shopping'
          })
        ),

        // Steps
        React.createElement('div', { className: 'steps-container' },
          ...steps.map((step, index) =>
            React.createElement('div', { key: index, className: 'step' },
              React.createElement('div', { className: 'step-icon' },
                React.createElement('span', { className: `icon ${step.icon} ${step.color}` })
              ),
              React.createElement('div', { className: 'step-content' },
                React.createElement('div', { className: 'step-header' },
                  React.createElement('span', { className: 'step-number' }, `Step ${index + 1}`),
                  React.createElement('div', { className: 'step-divider' })
                ),
                React.createElement('h3', { className: 'step-title' }, step.title),
                React.createElement('p', { className: 'step-description' }, step.description)
              )
            )
          )
        )
      ),

      // Stats bar
      React.createElement('div', { className: 'stats-bar' },
        React.createElement('div', { className: 'stats-grid' },
          React.createElement('div', { className: 'stat-item' },
            React.createElement('div', { className: 'stat-value emerald' }, '85%'),
            React.createElement('div', { className: 'stat-label' }, 'Less food waste')
          ),
          React.createElement('div', { className: 'stat-item' },
            React.createElement('div', { className: 'stat-value accent' }, '3.2hrs'),
            React.createElement('div', { className: 'stat-label' }, 'Saved per week')
          ),
          React.createElement('div', { className: 'stat-item' },
            React.createElement('div', { className: 'stat-value primary' }, '$180'),
            React.createElement('div', { className: 'stat-label' }, 'Average monthly savings')
          )
        )
      )
    )
  );
};

// Features Section Component
const FeaturesSection = () => {
  const features = [
    {
      icon: 'icon-scan',
      title: "Smart pantry scanning",
      description: "Quickly add items with our barcode scanner or voice input. Track quantities and expiration dates effortlessly.",
      color: "emerald"
    },
    {
      icon: 'icon-brain',
      title: "AI-powered meal planning",
      description: "Get personalized meal suggestions based on your preferences, dietary restrictions, and available ingredients.",
      color: "accent"
    },
    {
      icon: 'icon-calendar',
      title: "Weekly meal calendar",
      description: "Organize your meals with our intuitive calendar view. Drag, drop, and customize your weekly menu.",
      color: "primary"
    },
    {
      icon: 'icon-dollar',
      title: "Budget optimization",
      description: "Set spending limits and get meal plans that maximize nutrition while minimizing cost.",
      color: "emerald"
    },
    {
      icon: 'icon-clock',
      title: "Expiration alerts",
      description: "Never waste food again. Get timely notifications when items are approaching their expiration date.",
      color: "accent"
    },
    {
      icon: 'icon-utensils',
      title: "Recipe integration",
      description: "Access thousands of recipes tailored to your pantry items and dietary preferences.",
      color: "primary"
    },
    {
      icon: 'icon-chart',
      title: "Nutrition tracking",
      description: "Monitor your nutritional intake with detailed breakdowns of calories, macros, and micronutrients.",
      color: "emerald"
    },
    {
      icon: 'icon-shield',
      title: "Privacy focused",
      description: "Your data stays secure with end-to-end encryption. We never share your personal information.",
      color: "accent"
    }
  ];

  return React.createElement('section', { className: 'section gradient-subtle', id: 'features' },
    React.createElement('div', { className: 'container' },
      React.createElement('div', { className: 'section-header' },
        React.createElement('h2', { className: 'section-title' },
          'Everything you need to ',
          React.createElement('span', { className: 'gradient-text' }, 'master'),
          ' meal prep'
        ),
        React.createElement('p', { className: 'section-description' },
          'Powerful features designed to make meal planning effortless, budget-friendly, and perfectly tailored to your lifestyle.'
        )
      ),

      React.createElement('div', { className: 'features-grid' },
        ...features.map((feature, index) =>
          React.createElement('div', { key: index, className: 'feature-card' },
            React.createElement('div', { className: `feature-icon ${feature.color}` },
              React.createElement('span', { className: `icon ${feature.icon}` })
            ),
            React.createElement('h3', { className: 'feature-title' }, feature.title),
            React.createElement('p', { className: 'feature-description' }, feature.description)
          )
        )
      ),

      // Call to action
      React.createElement('div', { className: 'features-cta' },
        React.createElement('div', { className: 'features-cta-card' },
          React.createElement('h3', { className: 'features-cta-title' },
            'Ready to transform your meal planning?'
          ),
          React.createElement('p', { className: 'features-cta-description' },
            'Join thousands of users who\'ve already discovered the joy of stress-free, budget-conscious meal planning with Preppr.'
          ),
          React.createElement('a', { href: '/register', className: 'features-cta-button' },
            'Start your free trial'
          )
        )
      )
    )
  );
};

// Testimonials Section Component
const TestimonialsSection = () => {
  const testimonials = [
    {
      name: "Sarah Chen",
      role: "Graduate Student",
      content: "Preppr completely changed how I approach meal planning. As a busy grad student, I was constantly ordering takeout. Now I save over $200 a month and actually enjoy cooking!",
      rating: 5,
      image: "SC"
    },
    {
      name: "Marcus Rodriguez",
      role: "Software Engineer",
      content: "The AI meal planning is incredible. It suggests recipes based on what I actually have in my pantry and my dietary preferences. No more food waste!",
      rating: 5,
      image: "MR"
    },
    {
      name: "Emily Johnson",
      role: "Working Mom",
      content: "Managing meals for a family of four was overwhelming. Preppr's budget optimization and shopping lists have made grocery trips so much easier and more affordable.",
      rating: 5,
      image: "EJ"
    },
    {
      name: "David Kim",
      role: "College Student",
      content: "Perfect for dorm life! I can track everything in my mini fridge and get meal ideas that actually work with my tiny kitchen setup. Love the expiration alerts too.",
      rating: 5,
      image: "DK"
    },
    {
      name: "Lisa Thompson",
      role: "Fitness Enthusiast",
      content: "The nutrition tracking is spot-on. I can hit my macro goals while using ingredients I already have. It's made meal prep for my fitness goals so much simpler.",
      rating: 5,
      image: "LT"
    },
    {
      name: "Alex Martinez",
      role: "Young Professional",
      content: "I was skeptical about another app, but Preppr actually delivers. The weekly meal calendar keeps me organized and the recipe suggestions are always delicious.",
      rating: 5,
      image: "AM"
    }
  ];

  return React.createElement('section', { className: 'section', id: 'testimonials' },
    React.createElement('div', { className: 'container' },
      React.createElement('div', { className: 'section-header' },
        React.createElement('h2', { className: 'section-title' },
          'Loved by ',
          React.createElement('span', { className: 'gradient-text' }, 'thousands'),
          ' of home cooks'
        ),
        React.createElement('p', { className: 'section-description' },
          'See how Preppr is helping people save time, money, and stress while eating better than ever before.'
        )
      ),

      // Stats bar
      React.createElement('div', { className: 'testimonials-stats' },
        React.createElement('div', { className: 'stat-item' },
          React.createElement('div', { className: 'stat-value emerald' }, '50k+'),
          React.createElement('div', { className: 'stat-label' }, 'Active users')
        ),
        React.createElement('div', { className: 'stat-item' },
          React.createElement('div', { className: 'stat-value accent' }, '4.9★'),
          React.createElement('div', { className: 'stat-label' }, 'App store rating')
        ),
        React.createElement('div', { className: 'stat-item' },
          React.createElement('div', { className: 'stat-value primary' }, '2M+'),
          React.createElement('div', { className: 'stat-label' }, 'Meals planned')
        ),
        React.createElement('div', { className: 'stat-item' },
          React.createElement('div', { className: 'stat-value emerald' }, '$8M'),
          React.createElement('div', { className: 'stat-label' }, 'Total savings')
        )
      ),

      // Testimonials grid
      React.createElement('div', { className: 'testimonials-grid' },
        ...testimonials.map((testimonial, index) =>
          React.createElement('div', { key: index, className: 'testimonial-card' },
            React.createElement('div', { className: 'testimonial-rating' },
              ...Array(testimonial.rating).fill(0).map((_, i) =>
                React.createElement('span', { key: i, className: 'star' }, '⭐')
              )
            ),
            React.createElement('div', { className: 'testimonial-content' },
              React.createElement('p', { className: 'testimonial-quote' },
                `"${testimonial.content}"`
              )
            ),
            React.createElement('div', { className: 'testimonial-author' },
              React.createElement('div', { className: 'author-avatar' }, testimonial.image),
              React.createElement('div', { className: 'author-info' },
                React.createElement('div', { className: 'author-name' }, testimonial.name),
                React.createElement('div', { className: 'author-role' }, testimonial.role)
              )
            )
          )
        )
      ),

      // Bottom CTA
      React.createElement('div', { className: 'testimonials-cta' },
        React.createElement('div', { className: 'testimonials-badge' },
          React.createElement('span', { className: 'icon icon-star' }),
          'Join our happy community of home cooks'
        ),
        React.createElement('h3', { className: 'testimonials-cta-title' },
          'Ready to start your meal planning journey?'
        ),
        React.createElement('a', { href: '/register', className: 'testimonials-cta-button' },
          'Get started for free'
        )
      )
    )
  );
};

// Pricing Section Component
const PricingSection = () => {
  const plans = [
    {
      name: "Free Forever",
      price: "$0",
      period: "forever",
      description: "Perfect for getting started with meal planning",
      icon: 'icon-sparkles',
      features: [
        "Track up to 50 pantry items",
        "5 AI-generated meal plans per week",
        "Basic nutrition tracking",
        "Shopping list generation",
        "Recipe suggestions",
        "Mobile app access"
      ],
      cta: "Start for free",
      popular: false
    },
    {
      name: "Smart Planner",
      price: "$9",
      period: "per month",
      description: "For serious meal planners who want it all",
      icon: 'icon-zap',
      features: [
        "Unlimited pantry tracking",
        "Unlimited AI meal plans",
        "Advanced nutrition analytics",
        "Budget optimization tools",
        "Expiration date alerts",
        "Barcode scanning",
        "Recipe scaling",
        "Export shopping lists",
        "Priority customer support"
      ],
      cta: "Start 14-day free trial",
      popular: true
    },
    {
      name: "Family Plan",
      price: "$15",
      period: "per month",
      description: "For families who meal plan together",
      icon: 'icon-crown',
      features: [
        "Everything in Smart Planner",
        "Up to 6 family members",
        "Individual dietary preferences",
        "Shared pantry management",
        "Family meal calendar",
        "Kid-friendly recipe filtering",
        "Bulk meal planning",
        "Premium recipe collection"
      ],
      cta: "Start 14-day free trial",
      popular: false
    }
  ];

  return React.createElement('section', { className: 'section gradient-subtle', id: 'pricing' },
    React.createElement('div', { className: 'container' },
      React.createElement('div', { className: 'section-header' },
        React.createElement('h2', { className: 'section-title' },
          'Simple ',
          React.createElement('span', { className: 'gradient-text' }, 'transparent'),
          ' pricing'
        ),
        React.createElement('p', { className: 'section-description' },
          'Start free and upgrade when you\'re ready. No hidden fees, cancel anytime, and keep your data forever.'
        )
      ),

      React.createElement('div', { className: 'pricing-grid' },
        ...plans.map((plan, index) =>
          React.createElement('div', { 
            key: index, 
            className: `pricing-card ${plan.popular ? 'popular' : ''}` 
          },
            plan.popular && React.createElement('div', { className: 'popular-badge' }, 'Most popular'),
            
            React.createElement('div', { className: 'pricing-header' },
              React.createElement('div', { 
                className: `pricing-icon ${plan.popular ? 'popular' : 'default'}` 
              },
                React.createElement('span', { className: `icon ${plan.icon}` })
              ),
              React.createElement('h3', { className: 'pricing-name' }, plan.name),
              React.createElement('div', { className: 'pricing-price' },
                React.createElement('span', { className: 'price-amount' }, plan.price),
                React.createElement('span', { className: 'price-period' }, plan.period)
              ),
              React.createElement('p', { className: 'pricing-description' }, plan.description)
            ),

            React.createElement('ul', { className: 'pricing-features' },
              ...plan.features.map((feature, featureIndex) =>
                React.createElement('li', { key: featureIndex }, feature)
              )
            ),

            React.createElement('a', { 
              href: '/register', 
              className: `btn ${plan.popular ? 'btn-primary' : 'btn-secondary'} btn-lg`,
              style: { width: '100%' }
            }, plan.cta)
          )
        )
      ),

      // Additional info
      React.createElement('div', { className: 'pricing-info' },
        React.createElement('div', { className: 'pricing-info-card' },
          React.createElement('h3', { className: 'pricing-info-title' },
            'Questions about pricing?'
          ),
          React.createElement('p', { className: 'pricing-info-description' },
            'All plans include unlimited recipe access, cloud sync across devices, and regular feature updates. Students get 50% off any paid plan with valid student ID.'
          ),
          React.createElement('div', { className: 'pricing-info-buttons' },
            React.createElement('a', { href: '#', className: 'btn btn-ghost' }, 'Contact sales'),
            React.createElement('a', { href: '#', className: 'btn btn-secondary' }, 'View full feature comparison')
          )
        )
      )
    )
  );
};

// Footer Component
const Footer = () => {
  const footerLinks = {
    Product: [
      { name: "Features", href: "#features" },
      { name: "Pricing", href: "#pricing" },
      { name: "How it works", href: "#how-it-works" },
      { name: "Recipe database", href: "#recipes" }
    ],
    Company: [
      { name: "About us", href: "#about" },
      { name: "Blog", href: "#blog" },
      { name: "Careers", href: "#careers" },
      { name: "Press kit", href: "#press" }
    ],
    Support: [
      { name: "Help center", href: "#help" },
      { name: "Contact us", href: "#contact" },
      { name: "Community", href: "#community" },
      { name: "Student discount", href: "#student" }
    ],
    Legal: [
      { name: "Privacy policy", href: "#privacy" },
      { name: "Terms of service", href: "#terms" },
      { name: "Cookie policy", href: "#cookies" },
      { name: "Data security", href: "#security" }
    ]
  };

  return React.createElement('footer', { className: 'footer' },
    React.createElement('div', { className: 'container' },
      React.createElement('div', { className: 'footer-grid' },
        // Brand column
        React.createElement('div', { className: 'footer-brand' },
          React.createElement('div', { className: 'logo' },
            React.createElement('div', { className: 'logo-icon' }, 'P'),
            React.createElement('span', { className: 'logo-text' }, 'Preppr')
          ),
          React.createElement('p', { className: 'footer-description' },
            'Your AI-powered meal planning companion. Save time, money, and reduce food waste with smart meal planning.'
          ),
          React.createElement('div', { className: 'footer-social' },
            React.createElement('a', { href: '#', className: 'social-link' },
              React.createElement('span', { className: 'icon icon-twitter' })
            ),
            React.createElement('a', { href: '#', className: 'social-link' },
              React.createElement('span', { className: 'icon icon-instagram' })
            ),
            React.createElement('a', { href: '#', className: 'social-link' },
              React.createElement('span', { className: 'icon icon-mail' })
            )
          )
        ),

        // Links columns
        ...Object.entries(footerLinks).map(([category, links]) =>
          React.createElement('div', { key: category, className: 'footer-section' },
            React.createElement('h3', null, category),
            React.createElement('ul', { className: 'footer-links' },
              ...links.map(link =>
                React.createElement('li', { key: link.name },
                  React.createElement('a', { href: link.href }, link.name)
                )
              )
            )
          )
        )
      ),

      // Bottom section
      React.createElement('div', { className: 'footer-bottom' },
        React.createElement('div', { className: 'footer-love' },
          'Made with ',
          React.createElement('span', { className: 'heart' }, '❤️'),
          ' for better eating'
        ),
        React.createElement('div', { className: 'footer-copyright' },
          '© 2024 Preppr. All rights reserved.'
        )
      )
    )
  );
};

// Main App Component
const App = () => {
  return React.createElement('div', { className: 'min-h-screen' },
    React.createElement(Navigation),
    React.createElement('main', null,
      React.createElement(HeroSection),
      React.createElement(HowItWorksSection),
      React.createElement(FeaturesSection),
      React.createElement(TestimonialsSection),
      React.createElement(PricingSection)
    ),
    React.createElement(Footer)
  );
};

// Render the app
ReactDOM.render(React.createElement(App), document.getElementById('root'));