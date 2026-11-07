# frozen_string_literal: true

# Minimal Ruby client skeleton for mem20-ce.
# Talks to a running mem20-ce process or future HTTP gateway.

module Mem20CE
  VERSION = "0.1.0"

  class Client
    def initialize(store_path: File.expand_path("~/.mem20-ce/store"))
      @store_path = store_path
      # Future: spawn or connect to mem20-ce engine
    end

    def remember(content, tags: [])
      raise NotImplementedError, "Wire to mem20-ce CLI or HTTP in next increment"
    end

    def recall(query, k: 5)
      raise NotImplementedError, "Wire to mem20-ce CLI or HTTP in next increment"
    end

    def contamination
      raise NotImplementedError, "Wire to mem20-ce CLI or HTTP in next increment"
    end
  end
end
