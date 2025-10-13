"""
Enhanced Environment Variable Loading System
Provides comprehensive environment loading with fallback mechanisms and validation
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv, find_dotenv

logger = logging.getLogger(__name__)

class EnvironmentLoader:
    """
    Comprehensive environment variable loader with fallback mechanisms
    
    Features:
    - Multiple environment file support
    - Fallback loading order
    - Environment validation
    - Debug logging
    - System environment override detection
    """
    
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path(__file__).parent.parent.parent
        self.loaded_files = []
        self.overridden_vars = []
        self.missing_vars = []
        
    def load_environment(self, environment: str = None) -> bool:
        """
        Load environment variables with comprehensive fallback mechanism
        
        Args:
            environment: Specific environment to load (development, production, testing)
            
        Returns:
            bool: True if environment loaded successfully
        """
        logger.info("🚀 Starting environment variable loading process...")
        
        # Determine environment to load
        if not environment:
            environment = self._detect_environment()
        
        logger.info(f"🎯 Target environment: {environment}")
        
        # Define loading order with fallbacks
        env_files = self._get_environment_files(environment)
        
        # Load environment files in order
        success = self._load_environment_files(env_files)
        
        # Validate critical environment variables
        self._validate_environment()
        
        # Log environment loading results
        self._log_environment_status()
        
        return success
    
    def _detect_environment(self) -> str:
        """Detect current environment from various sources"""
        # Check system environment first
        flask_env = os.getenv('FLASK_ENV')
        if flask_env:
            logger.info(f"🔍 Detected FLASK_ENV from system: {flask_env}")
            return flask_env
        
        # Check for environment files
        if (self.base_path / 'env.development').exists():
            logger.info("🔍 Detected env.development file")
            return 'development'
        elif (self.base_path / 'env.production').exists():
            logger.info("🔍 Detected env.production file")
            return 'production'
        elif (self.base_path / 'env.testing').exists():
            logger.info("🔍 Detected env.testing file")
            return 'testing'
        
        # Default to development
        logger.info("🔍 No environment detected, defaulting to development")
        return 'development'
    
    def _get_environment_files(self, environment: str) -> List[Path]:
        """Get list of environment files to load in priority order"""
        files = []
        
        # 1. System environment variables (highest priority)
        files.append(None)  # Represents system environment
        
        # 2. Base .env file
        base_env = self.base_path / '.env'
        if base_env.exists():
            files.append(base_env)
        
        # 3. Environment-specific file
        env_file = self.base_path / f'env.{environment}'
        if env_file.exists():
            files.append(env_file)
        
        # 4. Development template
        dev_template = self.base_path / 'development.env'
        if dev_template.exists() and environment == 'development':
            files.append(dev_template)
        
        # 5. Production template
        prod_template = self.base_path / 'production.env'
        if prod_template.exists() and environment == 'production':
            files.append(prod_template)
        
        # 6. Fallback to python-dotenv find_dotenv
        dotenv_file = find_dotenv()
        if dotenv_file and Path(dotenv_file) not in files:
            files.append(Path(dotenv_file))
        
        logger.info(f"📁 Environment files to load: {[f.name if f else 'SYSTEM' for f in files]}")
        return files
    
    def _load_environment_files(self, env_files: List[Path]) -> bool:
        """Load environment files in priority order"""
        success = False
        
        for env_file in env_files:
            try:
                if env_file is None:
                    # System environment variables are already loaded
                    logger.debug("✅ System environment variables loaded")
                    success = True
                    continue
                
                if env_file.exists():
                    # Load specific environment file
                    load_dotenv(env_file, override=True)
                    self.loaded_files.append(env_file)
                    logger.info(f"✅ Loaded environment file: {env_file.name}")
                    success = True
                    
                    # Check for overridden variables
                    self._check_overridden_variables(env_file)
                    
                else:
                    logger.debug(f"⚠️ Environment file not found: {env_file}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to load environment file {env_file}: {e}")
        
        return success
    
    def _check_overridden_variables(self, env_file: Path):
        """Check which variables were overridden by this file"""
        try:
            with open(env_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        
                        # Check if this variable was previously set
                        if key in os.environ:
                            self.overridden_vars.append({
                                'key': key,
                                'file': env_file.name,
                                'line': line_num,
                                'previous_value': os.environ.get(key, 'NOT_SET')
                            })
        except Exception as e:
            logger.warning(f"⚠️ Could not check overridden variables in {env_file}: {e}")
    
    def _validate_environment(self):
        """Validate critical environment variables"""
        critical_vars = [
            'FLASK_ENV',
            'SECRET_KEY',
            'JWT_SECRET_KEY',
            'DATABASE_URL'
        ]
        
        for var in critical_vars:
            if not os.getenv(var):
                self.missing_vars.append(var)
                logger.warning(f"⚠️ Missing critical environment variable: {var}")
            else:
                logger.debug(f"✅ Found environment variable: {var}")
    
    def _log_environment_status(self):
        """Log comprehensive environment loading status"""
        logger.info("📊 Environment Loading Summary:")
        logger.info(f"   📁 Files loaded: {len(self.loaded_files)}")
        logger.info(f"   🔄 Variables overridden: {len(self.overridden_vars)}")
        logger.info(f"   ❌ Missing variables: {len(self.missing_vars)}")
        
        if self.loaded_files:
            logger.info("   📋 Loaded files:")
            for file in self.loaded_files:
                logger.info(f"      - {file.name}")
        
        if self.overridden_vars:
            logger.info("   🔄 Overridden variables:")
            for var in self.overridden_vars:
                logger.info(f"      - {var['key']} (from {var['file']}:{var['line']})")
        
        if self.missing_vars:
            logger.warning("   ❌ Missing critical variables:")
            for var in self.missing_vars:
                logger.warning(f"      - {var}")
        
        # Log current environment state
        current_env = os.getenv('FLASK_ENV', 'NOT_SET')
        debug_mode = os.getenv('DEBUG', 'NOT_SET')
        logger.info(f"   🎯 Current FLASK_ENV: {current_env}")
        logger.info(f"   🐛 Current DEBUG: {debug_mode}")
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get comprehensive environment information for debugging"""
        return {
            'current_environment': os.getenv('FLASK_ENV', 'NOT_SET'),
            'debug_mode': os.getenv('DEBUG', 'NOT_SET'),
            'loaded_files': [str(f) for f in self.loaded_files],
            'overridden_variables': self.overridden_vars,
            'missing_variables': self.missing_vars,
            'system_environment': dict(os.environ)
        }
    
    def force_environment(self, environment: str):
        """Force set environment variables for development"""
        if environment == 'development':
            os.environ['FLASK_ENV'] = 'development'
            os.environ['DEBUG'] = 'true'
            os.environ['TESTING'] = 'false'
            logger.info(f"🔧 Forced environment to: {environment}")
        elif environment == 'production':
            os.environ['FLASK_ENV'] = 'production'
            os.environ['DEBUG'] = 'false'
            os.environ['TESTING'] = 'false'
            logger.info(f"🔧 Forced environment to: {environment}")

# Global environment loader instance
env_loader = EnvironmentLoader()

def load_environment(environment: str = None) -> bool:
    """
    Load environment variables using the global environment loader
    
    Args:
        environment: Specific environment to load
        
    Returns:
        bool: True if environment loaded successfully
    """
    return env_loader.load_environment(environment)

def get_environment_info() -> Dict[str, Any]:
    """Get environment information for debugging"""
    return env_loader.get_environment_info()

def force_development_mode():
    """Force development mode for debugging"""
    env_loader.force_environment('development')

def force_production_mode():
    """Force production mode"""
    env_loader.force_environment('production')
