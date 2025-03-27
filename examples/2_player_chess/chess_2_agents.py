from stockfish import Stockfish
from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig
from moya.orchestrators.simple_orchestrator import SimpleOrchestrator
from moya.registry.agent_registry import AgentRegistry
from moya.tools.tool_registry import ToolRegistry
from moya.tools.base_tool import BaseTool
import os
import chess

# Set the path to your Stockfish executable
STOCKFISH_PATH = os.environ.get("STOCKFISH_PATH")
GAME_IMAGES_PATH = "./game_images"

stockfish = Stockfish(STOCKFISH_PATH)

def get_top_moves_from_fen(fen, n=5):
    """
    Retrieves the top N best moves from a given FEN (Forsyth-Edwards Notation) string 
    using the Stockfish chess engine.
    This function sets the board position based on the provided FEN string, adjusts 
    the Stockfish skill level to the maximum (20), and then retrieves the top N best 
    moves as evaluated by the engine.
    Args:
        - fen (str): The FEN string representing the current board position.
        - n (int, optional): The number of top moves to retrieve. Defaults to 5.
    Returns:
        str: A string representation of the top N best moves as evaluated by Stockfish.
    Raises:
        Exception: If an error occurs during the process of setting the FEN position 
                   or retrieving the top moves, it will be caught and printed.
    """
    
    try:
        stockfish.set_fen_position(fen)  # Set the board position
        stockfish.set_skill_level(20)  # Set skill level (0-20)
        
        # Get top N best moves
        top_moves = stockfish.get_top_moves(n)
        print("Top moves", top_moves)
        return str(top_moves)
    except Exception as e:
        print("Error in get_top_moves:", e)

def moves_to_fen(moves):
    """Convert a list of moves to FEN notation using the chess library."""
    board = chess.Board()  # Start with the initial position
    for move in moves:
        board.push_san(move)  # Apply each move in Standard Algebraic Notation (SAN)
    return board.fen()  # Get the final FEN notation

def fen_to_board(fen, move_number):
    """
    Convert FEN notation to a chess board and save it as an SVG file.

    This function generates an SVG representation of the chess board based on the 
    provided FEN notation and saves it in a folder named 'game_images'. Each image 
    is named sequentially as 'image_{n}.svg', where 'n' corresponds to the move number.

    Args:
        fen (str): The FEN string representing the current board position.
        move_number (int): The move number used to name the SVG file.

    Returns:
        None
    """
    # Ensure the game_images directory exists
    os.makedirs(GAME_IMAGES_PATH, exist_ok=True)
    
    board = chess.Board(fen)
    board_svg = board._repr_svg_()  # SVG representation of the board
    
    # Save the SVG file with the name image_{n}.svg
    file_path = os.path.join(GAME_IMAGES_PATH, f"image_{move_number}.svg")
    with open(file_path, "w") as f:
        f.write(board_svg)

def generate_md_file_for_game():
    """
    Generate a Markdown file to display the chess game images in sequence.

    This function creates a Markdown file that includes the SVG images of the chess 
    board for each move in the game. The Markdown file is saved as 'chess_game.md' 
    in the same directory as the images.

    Args:
        images_path (str): The path to the directory containing the SVG images.

    Returns:
        None
    """
    image_files = os.listdir(GAME_IMAGES_PATH)

    number_of_images = len(image_files)
    

    # Generate Markdown content with image links
    markdown_content = "\n".join([f"![Move {i}](game_images/image_{i}.svg)" for i in range(1, number_of_images + 1)])

    # Save the Markdown content to a file
    with open("chess_game.md", "w") as f:
        f.write(markdown_content)

def check_game_over(fen):
    """Check if the game is over based on the FEN position."""
    board = chess.Board(fen)
    if board.is_checkmate():
        return  "Checkmate"
    if board.is_stalemate():
        return "Stalemate" 
    return None

def create_chess_agent(agent_name, description, tool_registry) -> OpenAIAgent:
    """Create a chess-playing agent."""
    agent_config = OpenAIAgentConfig(
        agent_name=agent_name,
        agent_type="ChatAgent",
        description=description,
        system_prompt="""You are a chess-playing assistant. 
        Your job is to play chess moves based on the current FEN position.
        You will receive the FEN notation and should return the best move. 
        Respond with only the move.
        Do not provide any explanation or additional text. 
        Use the 'GetTopMoves' tool to get the top moves for the current position. 
        The tool accepts the FEN notation and returns the top moves with evaluations.
        Provide the FEN notation to the tool to get the top moves. Pick one of the top moves as your response.
        The response provided should be one of the top moves. Do not deviate from the top moves provided by the tool.
        Example output from the tool: 
        <example>
       [{"Move": "e2e5", "Centipawn": None, "Mate": 8}, {"Move": "b3a5", "Centipawn": 896, "Mate": None}, {"Move": "f8b4", "Centipawn": 852, "Mate": None}, {"Move": "c2c3", "Centipawn": 840, "Mate": None}, {"Move": "b3c5", "Centipawn": 840, "Mate": None}]
        </example>
        You are supposed to pick one of the moves from the list. Each item in the list is a dictionary with keys 'Move', 'Centipawn', and 'Mate'. Respond with the 'Move' key value of the move you chose to be the best.
        """,
        llm_config={
            'temperature': 0.1
        },
        model_name="gpt-4o",
        api_key=os.getenv("OPENAI_API_KEY"),
        tool_registry=tool_registry
    )
    return OpenAIAgent(config=agent_config)

def setup_chess_orchestrator():
    """Set up the multi-agent orchestrator for chess."""
    # Set up tool registry
    tool_registry = ToolRegistry()
    tool_registry.register_tool(BaseTool(name="GetTopMoves", function=get_top_moves_from_fen))

    # Set up agent registry
    registry = AgentRegistry()
    registry.register_agent(create_chess_agent("WhiteAgent", "Plays as White", tool_registry))
    registry.register_agent(create_chess_agent("BlackAgent", "Plays as Black", tool_registry))

    # Create and configure the orchestrator
    orchestrator = SimpleOrchestrator(
        agent_registry=registry,
        default_agent_name="WhiteAgent"
    )
    return orchestrator

def play_chess_game():
    """Simulate a chess game between two agents."""
    orchestrator = setup_chess_orchestrator()
    moves = []
    stockfish = Stockfish(STOCKFISH_PATH)
    fen = stockfish.get_fen_position()  # Start with the initial position
    thread_id = "chess_game"

    while True:
        # Alternate between White and Black agents
        current_agent_name = "WhiteAgent" if len(moves) % 2 == 0 else "BlackAgent"

        # Enrich input with the current FEN
        enriched_input = f"Current FEN: {fen}. Find the best move."
        print("Enriched input:", enriched_input)

        # Get the agent's move
        response = orchestrator.orchestrate(
            thread_id=thread_id,
            user_message=enriched_input
        )
        move = response.strip()

        moves.append(move)
        print(f"{current_agent_name} played: {move}")

        # Update the FEN
        fen = moves_to_fen(moves)

        # Save board
        fen_to_board(fen, len(moves))
        

        # Check for game end (e.g., checkmate, stalemate)
        stockfish.set_fen_position(fen)
        game_status = check_game_over(fen)

        if game_status:
            if game_status == "Checkmate":
                print(f"Checkmate! {current_agent_name} wins.")
            elif game_status == "Stalemate":
                print("Stalemate! The game is a draw.")
            break


if __name__ == "__main__":
    play_chess_game()
    generate_md_file_for_game()