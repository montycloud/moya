
import { motion } from 'framer-motion';
import ThemeSwitcher from './ThemeSwitcher';

const Header = () => {
  return (
    <header className="h-header flex items-center justify-between py-4 mb-4">
      <motion.div 
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5 }}
        className="flex items-center"
      >
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center mr-3 shadow-lg">
          <svg width="24" height="24" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M24 24L40 16L56 24V56L40 64L24 56V24Z" stroke="white" strokeWidth="2" strokeLinejoin="round" />
            <path d="M40 16V40M40 64V40M24 24L40 32M56 24L40 32M40 32V40" stroke="white" strokeWidth="2" strokeLinejoin="round" />
            <circle cx="40" cy="40" r="6" fill="white" />
          </svg>
        </div>
        <div>
          <h1 className="text-xl font-semibold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">Moya</h1>
          <p className="text-xs text-muted-foreground">CloudOps AI Framework</p>
        </div>
      </motion.div>
      
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="flex items-center space-x-2"
      >
        <ThemeSwitcher />
        
        <a 
          href="https://github.com/moya-ai/framework" 
          target="_blank" 
          rel="noopener noreferrer"
          className="text-sm text-muted-foreground hover:text-foreground transition-colors px-3 py-2 rounded-md hover:bg-secondary/50"
        >
          GitHub
        </a>
        <a 
          href="https://moya-ai.docs.com" 
          target="_blank" 
          rel="noopener noreferrer"
          className="text-sm text-foreground hover:text-primary transition-colors px-3 py-2 ml-2 rounded-md bg-primary/10 hover:bg-primary/20"
        >
          Documentation
        </a>
      </motion.div>
    </header>
  );
};

export default Header;
