# Makefile for packaging Lambda functions with conditional rebuilds

LAMBDA_SRC_DIR = lambdas
BUILD_DIR = build

SCRAPER_SRC = $(LAMBDA_SRC_DIR)/scraper_lambda.py
PROCESSOR_SRC = $(LAMBDA_SRC_DIR)/processor_lambda.py
LLM_SRC = $(LAMBDA_SRC_DIR)/llm_analysis_lambda.py
NOTIFIER_SRC = $(LAMBDA_SRC_DIR)/notifier_lambda.py
REQUIREMENTS = $(LAMBDA_SRC_DIR)/requirements.txt

SCRAPER_ZIP = $(BUILD_DIR)/scraper_lambda.zip
PROCESSOR_ZIP = $(BUILD_DIR)/processor_lambda.zip
LLM_ZIP = $(BUILD_DIR)/llm_analysis_lambda.zip
NOTIFIER_ZIP = $(BUILD_DIR)/notifier_lambda.zip

.PHONY: all clean scraper processor llm_analysis_lambda notifier_lambda

all: $(SCRAPER_ZIP) $(PROCESSOR_ZIP) $(LLM_ZIP) $(NOTIFIER_ZIP)
	@echo "All Lambdas packaged!"

# --- Conditional packaging for Lambdas with dependencies ---
$(SCRAPER_ZIP): $(SCRAPER_SRC) $(REQUIREMENTS)
	@echo "Packaging scraper Lambda..."
	@mkdir -p $(BUILD_DIR)/temp_scraper
	@rm -f $(SCRAPER_ZIP)
	pip install --target $(BUILD_DIR)/temp_scraper -r $(REQUIREMENTS)
	cp $(SCRAPER_SRC) $(BUILD_DIR)/temp_scraper/
	cd $(BUILD_DIR)/temp_scraper && zip -r ../scraper_lambda.zip *
	rm -rf $(BUILD_DIR)/temp_scraper
	@echo "$(SCRAPER_ZIP) created!"

$(PROCESSOR_ZIP): $(PROCESSOR_SRC) $(REQUIREMENTS)
	@echo "Packaging processor Lambda..."
	@mkdir -p $(BUILD_DIR)/temp_processor
	@rm -f $(PROCESSOR_ZIP)
	pip install --target $(BUILD_DIR)/temp_processor -r $(REQUIREMENTS)
	cp $(PROCESSOR_SRC) $(BUILD_DIR)/temp_processor/
	cd $(BUILD_DIR)/temp_processor && zip -r ../processor_lambda.zip *
	rm -rf $(BUILD_DIR)/temp_processor
	@echo "$(PROCESSOR_ZIP) created!"

$(LLM_ZIP): $(LLM_SRC)
	@echo "Packaging llm_analysis Lambda..."
	@mkdir -p $(BUILD_DIR)/temp_llm_analysis
	@rm -f $(LLM_ZIP)
	pip install --target $(BUILD_DIR)/temp_llm_analysis requests
	cp $(LLM_SRC) $(BUILD_DIR)/temp_llm_analysis/
	cd $(BUILD_DIR)/temp_llm_analysis && zip -r ../llm_analysis_lambda.zip *
	rm -rf $(BUILD_DIR)/temp_llm_analysis
	@echo "$(LLM_ZIP) created!"

$(NOTIFIER_ZIP): $(NOTIFIER_SRC)
	@echo "Packaging notifier Lambda..."
	@mkdir -p $(BUILD_DIR)/temp_notifier
	@rm -f $(NOTIFIER_ZIP)
	cp $(NOTIFIER_SRC) $(BUILD_DIR)/temp_notifier/
	cd $(BUILD_DIR)/temp_notifier && zip -r ../notifier_lambda.zip *
	rm -rf $(BUILD_DIR)/temp_notifier
	@echo "$(NOTIFIER_ZIP) created!"

clean:
	@echo "Cleaning build folder..."
	@rm -rf $(BUILD_DIR)/*
	@echo "Done."
