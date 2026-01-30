import { useState } from 'react'
import { Link } from 'react-router-dom'
import './Home.css'

export default function Home() {
  const [activeSection, setActiveSection] = useState('home')

  return (
    <div className="home-page">
      <section id="home" className="hero">
        <div className="hero-content">
          <h1 className="hero-title">Powering the Future</h1>
          <p className="hero-subtitle">
            Innovative energy solutions for a sustainable tomorrow
          </p>
          <div className="hero-buttons">
            <Link to="/dashboard" className="btn btn-primary">View Dashboard</Link>
            <Link to="/reports" className="btn btn-secondary">Reports</Link>
            <Link to="/customers" className="btn btn-secondary">Customer Portal</Link>
          </div>
        </div>
        <div className="hero-visual">
          <div className="energy-wave"></div>
        </div>
      </section>

      <section id="services" className="services">
        <div className="container">
          <h2 className="section-title">Our Services</h2>
          <div className="services-grid">
            <div className="service-card">
              <div className="service-icon">🌱</div>
              <h3>Renewable Energy</h3>
              <p>Solar, wind, and hydroelectric solutions tailored to your needs</p>
            </div>
            <div className="service-card">
              <div className="service-icon">🔋</div>
              <h3>Energy Storage</h3>
              <p>Advanced battery systems for reliable power management</p>
            </div>
            <div className="service-card">
              <div className="service-icon">⚡</div>
              <h3>Smart Grid Solutions</h3>
              <p>Intelligent energy distribution and monitoring systems</p>
            </div>
            <div className="service-card">
              <div className="service-icon">🏭</div>
              <h3>Industrial Solutions</h3>
              <p>Custom energy systems for commercial and industrial clients</p>
            </div>
            <div className="service-card">
              <div className="service-icon">📊</div>
              <h3>Energy Reports</h3>
              <p>Comprehensive analysis and anomaly detection for equipment monitoring</p>
              <Link to="/reports/wilson-center" className="btn btn-primary" style={{ marginTop: '1rem' }}>
                Wilson Center Report
              </Link>
            </div>
          </div>
        </div>
      </section>

      <section id="about" className="about">
        <div className="container">
          <h2 className="section-title">About Argo Energy Solutions</h2>
          <div className="about-content">
            <div className="about-text">
              <p>
                Argo Energy Solutions is a leading provider of innovative energy 
                technologies and services. We specialize in delivering sustainable, 
                efficient, and cost-effective energy solutions that help businesses 
                and communities reduce their carbon footprint while improving their 
                bottom line.
              </p>
              <p>
                With years of experience in the energy sector, our team of experts 
                is dedicated to helping you navigate the transition to clean energy 
                with confidence and ease.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section id="contact" className="contact">
        <div className="container">
          <h2 className="section-title">Get In Touch</h2>
          <div className="contact-content">
            <form className="contact-form">
              <div className="form-group">
                <label htmlFor="name">Name</label>
                <input type="text" id="name" name="name" required />
              </div>
              <div className="form-group">
                <label htmlFor="email">Email</label>
                <input type="email" id="email" name="email" required />
              </div>
              <div className="form-group">
                <label htmlFor="message">Message</label>
                <textarea id="message" name="message" rows={5} required></textarea>
              </div>
              <button type="submit" className="btn btn-primary">Send Message</button>
            </form>
          </div>
        </div>
      </section>
    </div>
  )
}

