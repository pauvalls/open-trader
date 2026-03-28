"""DEX Service - Multi-DEX trading interface

Soporta:
- Uniswap V3 (Ethereum, Arbitrum, Base, Optimism, Polygon)
- PancakeSwap V3 (BSC, Arbitrum, Base)
- SushiSwap V3 (Ethereum, Arbitrum, Base, Optimism, Polygon)

Simple cambio de DEX mediante factory pattern.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, List, Callable
from decimal import Decimal
import json
from web3 import Web3
from eth_account import Account
import os


@dataclass
class DEXConfig:
    """Configuración para un DEX en una red específica"""
    name: str
    chain: str  # ethereum, arbitrum, base, bsc, optimism, polygon
    router_address: str
    factory_address: str
    quoter_address: Optional[str] = None
    rpc_url: Optional[str] = None
    explorer_url: Optional[str] = None
    native_token: str = "ETH"
    
    # Fees por defecto (en bps)
    default_fee_tier: int = 3000  # 0.3%
    
    # Configuración de gas
    gas_limit_multiplier: float = 1.2
    max_priority_fee_gwei: float = 0.1


@dataclass
class SwapQuote:
    """Cotización de swap"""
    input_amount: Decimal
    output_amount: Decimal
    price: Decimal
    price_impact: float
    fee_tier: int
    route: List[str]
    estimated_gas: int


@dataclass
class SwapResult:
    """Resultado de swap ejecutado"""
    success: bool
    tx_hash: Optional[str]
    input_amount: Decimal
    output_amount: Decimal
    effective_price: Decimal
    gas_used: int
    gas_cost_eth: Decimal
    error: Optional[str] = None


class BaseDEXAdapter(ABC):
    """Interfaz base para cualquier DEX"""
    
    def __init__(self, config: DEXConfig, private_key: Optional[str] = None):
        self.config = config
        self.w3 = Web3(Web3.HTTPProvider(config.rpc_url))
        
        if private_key:
            self.account = Account.from_key(private_key)
            self.address = self.account.address
        else:
            self.account = None
            self.address = None
        
        # ABIs mínimos (solo funciones necesarias)
        self.router_abi = self._get_router_abi()
        self.erc20_abi = self._get_erc20_abi()
        
        self.router = self.w3.eth.contract(
            address=Web3.to_checksum_address(config.router_address),
            abi=self.router_abi
        )
    
    @abstractmethod
    def _get_router_abi(self) -> List[Dict]:
        """Retorna ABI del router específico del DEX"""
        pass
    
    def _get_erc20_abi(self) -> List[Dict]:
        """ABI estándar ERC20"""
        return [
            {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
            {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
            {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
            {"constant": True, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
        ]
    
    @abstractmethod
    async def get_quote(
        self,
        token_in: str,
        token_out: str,
        amount_in: Decimal,
        fee_tier: Optional[int] = None
    ) -> SwapQuote:
        """Obtener cotización para un swap"""
        pass
    
    @abstractmethod
    async def execute_swap(
        self,
        token_in: str,
        token_out: str,
        amount_in: Decimal,
        min_amount_out: Decimal,
        fee_tier: Optional[int] = None,
        deadline_seconds: int = 300
    ) -> SwapResult:
        """Ejecutar swap"""
        pass
    
    async def get_token_balance(self, token_address: str) -> Decimal:
        """Obtener balance de un token"""
        if token_address.lower() == "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee":
            # Native token (ETH, BNB, etc.)
            balance_wei = self.w3.eth.get_balance(self.address)
            return Decimal(balance_wei) / Decimal(10**18)
        
        token = self.w3.eth.contract(address=token_address, abi=self.erc20_abi)
        decimals = token.functions.decimals().call()
        balance = token.functions.balanceOf(self.address).call()
        return Decimal(balance) / Decimal(10**decimals)
    
    async def approve_token(
        self,
        token_address: str,
        spender_address: str,
        amount: Decimal
    ) -> Optional[str]:
        """Aprobar gasto de token. Retorna tx_hash o None si ya está aprobado."""
        token = self.w3.eth.contract(address=token_address, abi=self.erc20_abi)
        decimals = token.functions.decimals().call()
        amount_wei = int(amount * Decimal(10**decimals))
        
        current_allowance = token.functions.allowance(self.address, spender_address).call()
        if current_allowance >= amount_wei:
            return None  # Ya aprobado suficiente
        
        # Aprobar cantidad máxima
        tx = token.functions.approve(
            spender_address,
            2**256 - 1  # Max uint256
        ).build_transaction({
            'from': self.address,
            'nonce': self.w3.eth.get_transaction_count(self.address),
            'gas': 100000,
            'maxFeePerGas': self.w3.eth.gas_price * 2,
            'maxPriorityFeePerGas': self.w3.to_wei(self.config.max_priority_fee_gwei, 'gwei'),
        })
        
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return tx_hash.hex()
    
    def _get_deadline(self, seconds: int = 300) -> int:
        """Obtener timestamp límite para transacción"""
        import time
        return int(time.time()) + seconds


class UniswapV3Adapter(BaseDEXAdapter):
    """Adapter para Uniswap V3"""
    
    FEE_TIERS = {
        100: 0.01,    # 0.01% - stable pairs
        500: 0.05,    # 0.05% - stable/volatile
        3000: 0.3,    # 0.3%  - most pairs
        10000: 1.0,   # 1.0%  - exotic
    }
    
    def _get_router_abi(self) -> List[Dict]:
        # ABI simplificado de Uniswap V3 Router
        return json.loads('''[
            {"inputs": [{"internalType": "address", "name": "_factory", "type": "address"}, {"internalType": "address", "name": "_WETH9", "type": "address"}], "stateMutability": "nonpayable", "type": "constructor"},
            {"inputs": [{"components": [{"internalType": "address", "name": "tokenIn", "type": "address"}, {"internalType": "address", "name": "tokenOut", "type": "address"}, {"internalType": "uint24", "name": "fee", "type": "uint24"}, {"internalType": "address", "name": "recipient", "type": "address"}, {"internalType": "uint256", "name": "deadline", "type": "uint256"}, {"internalType": "uint256", "name": "amountIn", "type": "uint256"}, {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"}, {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}], "internalType": "struct ISwapRouter.ExactInputSingleParams", "name": "params", "type": "tuple"}], "name": "exactInputSingle", "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}], "stateMutability": "payable", "type": "function"},
            {"inputs": [{"internalType": "address", "name": "token", "type": "address"}, {"internalType": "uint256", "name": "amountMinimum", "type": "uint256"}, {"internalType": "address", "name": "recipient", "type": "address"}], "name": "sweepToken", "outputs": [], "stateMutability": "payable", "type": "function"}
        ]''')
    
    async def get_quote(
        self,
        token_in: str,
        token_out: str,
        amount_in: Decimal,
        fee_tier: Optional[int] = None
    ) -> SwapQuote:
        """Para Uniswap V3, necesitamos quoter o llamada estática"""
        # Simplificado: usar llamada estática al router
        # En producción usar QuoterV2 para precisión
        
        if fee_tier is None:
            fee_tier = self.config.default_fee_tier
        
        # Estimación simple (en producción usar quoter)
        # Asumiendo 0.3% de slippage + fees
        fee_pct = self.FEE_TIERS.get(fee_tier, 0.3)
        estimated_output = amount_in * Decimal(0.997 - fee_pct/100)
        
        return SwapQuote(
            input_amount=amount_in,
            output_amount=estimated_output,
            price=estimated_output / amount_in if amount_in > 0 else Decimal(0),
            price_impact=0.3,
            fee_tier=fee_tier,
            route=[token_in, token_out],
            estimated_gas=150000
        )
    
    async def execute_swap(
        self,
        token_in: str,
        token_out: str,
        amount_in: Decimal,
        min_amount_out: Decimal,
        fee_tier: Optional[int] = None,
        deadline_seconds: int = 300
    ) -> SwapResult:
        """Ejecutar swap exactInputSingle en Uniswap V3"""
        if not self.account:
            return SwapResult(success=False, tx_hash=None, error="No wallet configured")
        
        try:
            if fee_tier is None:
                fee_tier = self.config.default_fee_tier
            
            # Convertir amounts a wei
            # Asumimos 18 decimales para simplificar (en producción obtener decimales reales)
            amount_in_wei = int(amount_in * Decimal(10**18))
            min_out_wei = int(min_amount_out * Decimal(10**18))
            
            params = {
                'tokenIn': Web3.to_checksum_address(token_in),
                'tokenOut': Web3.to_checksum_address(token_out),
                'fee': fee_tier,
                'recipient': self.address,
                'deadline': self._get_deadline(deadline_seconds),
                'amountIn': amount_in_wei,
                'amountOutMinimum': min_out_wei,
                'sqrtPriceLimitX96': 0  # No price limit
            }
            
            tx = self.router.functions.exactInputSingle(params).build_transaction({
                'from': self.address,
                'nonce': self.w3.eth.get_transaction_count(self.address),
                'gas': 200000,
                'maxFeePerGas': self.w3.eth.gas_price * 2,
                'maxPriorityFeePerGas': self.w3.to_wei(self.config.max_priority_fee_gwei, 'gwei'),
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            gas_cost_eth = Decimal(receipt.gasUsed) * Decimal(self.w3.eth.gas_price) / Decimal(10**18)
            
            return SwapResult(
                success=receipt.status == 1,
                tx_hash=tx_hash.hex(),
                input_amount=amount_in,
                output_amount=min_amount_out,  # Estimado
                effective_price=min_amount_out / amount_in if amount_in > 0 else Decimal(0),
                gas_used=receipt.gasUsed,
                gas_cost_eth=gas_cost_eth
            )
            
        except Exception as e:
            return SwapResult(
                success=False,
                tx_hash=None,
                input_amount=amount_in,
                output_amount=Decimal(0),
                effective_price=Decimal(0),
                gas_used=0,
                gas_cost_eth=Decimal(0),
                error=str(e)
            )


class PancakeSwapV3Adapter(UniswapV3Adapter):
    """PancakeSwap V3 usa el mismo código base que Uniswap V3"""
    
    FEE_TIERS = {
        100: 0.01,
        500: 0.05,
        2500: 0.25,  # Pancake tiene 0.25%
        10000: 1.0,
    }


class SushiSwapV3Adapter(UniswapV3Adapter):
    """SushiSwap V3 también basado en Uniswap V3"""
    pass


# ============================================================================
# CONFIGURACIONES DE REDES Y DEXs
# ============================================================================

DEX_CONFIGS = {
    # Uniswap V3
    "uniswap-ethereum": DEXConfig(
        name="Uniswap V3",
        chain="ethereum",
        router_address="0xE592427A0AEce92De3Edee1F18E0157C05861564",
        factory_address="0x1F98431c8aD98523631AE4a59f267346ea31F984",
        rpc_url=os.getenv("ETHEREUM_RPC", "https://eth.llamarpc.com"),
        explorer_url="https://etherscan.io",
        native_token="ETH"
    ),
    "uniswap-arbitrum": DEXConfig(
        name="Uniswap V3",
        chain="arbitrum",
        router_address="0xE592427A0AEce92De3Edee1F18E0157C05861564",
        factory_address="0x1F98431c8aD98523631AE4a59f267346ea31F984",
        rpc_url=os.getenv("ARBITRUM_RPC", "https://arb1.arbitrum.io/rpc"),
        explorer_url="https://arbiscan.io",
        native_token="ETH",
        default_fee_tier=500  # 0.05% en Arbitrum es más común
    ),
    "uniswap-base": DEXConfig(
        name="Uniswap V3",
        chain="base",
        router_address="0x2626664c2603336E57B271c5C0b26F421741e481",
        factory_address="0x33128a8fC17869897dcE68Ed026d694621f6FDfD",
        rpc_url=os.getenv("BASE_RPC", "https://mainnet.base.org"),
        explorer_url="https://basescan.org",
        native_token="ETH"
    ),
    "uniswap-optimism": DEXConfig(
        name="Uniswap V3",
        chain="optimism",
        router_address="0xE592427A0AEce92De3Edee1F18E0157C05861564",
        factory_address="0x1F98431c8aD98523631AE4a59f267346ea31F984",
        rpc_url=os.getenv("OPTIMISM_RPC", "https://mainnet.optimism.io"),
        explorer_url="https://optimistic.etherscan.io",
        native_token="ETH"
    ),
    "uniswap-polygon": DEXConfig(
        name="Uniswap V3",
        chain="polygon",
        router_address="0xE592427A0AEce92De3Edee1F18E0157C05861564",
        factory_address="0x1F98431c8aD98523631AE4a59f267346ea31F984",
        rpc_url=os.getenv("POLYGON_RPC", "https://polygon-rpc.com"),
        explorer_url="https://polygonscan.com",
        native_token="MATIC"
    ),
    
    # PancakeSwap V3
    "pancakeswap-bsc": DEXConfig(
        name="PancakeSwap V3",
        chain="bsc",
        router_address="0x1b81D678ffb9C0263b24A97847620C99d213eB14",
        factory_address="0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865",
        rpc_url=os.getenv("BSC_RPC", "https://bsc-dataseed.binance.org"),
        explorer_url="https://bscscan.com",
        native_token="BNB",
        default_fee_tier=2500  # 0.25%
    ),
    "pancakeswap-arbitrum": DEXConfig(
        name="PancakeSwap V3",
        chain="arbitrum",
        router_address="0x1b81D678ffb9C0263b24A97847620C99d213eB14",
        factory_address="0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865",
        rpc_url=os.getenv("ARBITRUM_RPC", "https://arb1.arbitrum.io/rpc"),
        explorer_url="https://arbiscan.io",
        native_token="ETH"
    ),
    "pancakeswap-base": DEXConfig(
        name="PancakeSwap V3",
        chain="base",
        router_address="0x1b81D678ffb9C0263b24A97847620C99d213eB14",
        factory_address="0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865",
        rpc_url=os.getenv("BASE_RPC", "https://mainnet.base.org"),
        explorer_url="https://basescan.org",
        native_token="ETH"
    ),
    
    # SushiSwap V3
    "sushiswap-ethereum": DEXConfig(
        name="SushiSwap V3",
        chain="ethereum",
        router_address="0xbACEB8eC6b9355Dfc0269C18bac9d6E2Bdc29C4F",
        factory_address="0xbACEB8eC6b9355Dfc0269C18bac9d6E2Bdc29C4F",
        rpc_url=os.getenv("ETHEREUM_RPC", "https://eth.llamarpc.com"),
        explorer_url="https://etherscan.io",
        native_token="ETH"
    ),
    "sushiswap-arbitrum": DEXConfig(
        name="SushiSwap V3",
        chain="arbitrum",
        router_address="0x6BDED42c6DA8FBf0d2bA55B2fa120C5e0c8D7891",
        factory_address="0x1af415f1EAa0BEE8c4f8E5C37b8A75E31C74d24E",
        rpc_url=os.getenv("ARBITRUM_RPC", "https://arb1.arbitrum.io/rpc"),
        explorer_url="https://arbiscan.io",
        native_token="ETH"
    ),
    "sushiswap-base": DEXConfig(
        name="SushiSwap V3",
        chain="base",
        router_address="0xFB7eF66a7e61224DD6FcD0D7d9C3be5C8B049b9f",
        factory_address="0xc35DADB65012eC5796536bD9864eD8773aBc74C4",
        rpc_url=os.getenv("BASE_RPC", "https://mainnet.base.org"),
        explorer_url="https://basescan.org",
        native_token="ETH"
    ),
}


# Mapeo de símbolos a direcciones (ejemplo - ampliar según necesidad)
TOKEN_ADDRESSES = {
    "ethereum": {
        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
        "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        "LINK": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
        "UNI": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
    },
    "arbitrum": {
        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
        "USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        "USDT": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
        "DAI": "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
        "WBTC": "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f",
        "ARB": "0x912CE59144191C1204E64559FE8253a0e49E6548",
        "LINK": "0xf97f4df75117a78c1A5a0DBb814Af92458539FB4",
    },
    "base": {
        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "WETH": "0x4200000000000000000000000000000000000006",
        "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "DAI": "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
        "cbETH": "0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22",
    },
    "bsc": {
        "BNB": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "WBNB": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
        "USDT": "0x55d398326f99059fF775485246999027B3197955",
        "BUSD": "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56",
        "CAKE": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82",
    },
}


def get_dex_adapter(dex_id: str, private_key: Optional[str] = None) -> BaseDEXAdapter:
    """
    Factory para obtener adapter de DEX.
    
    Args:
        dex_id: Identificador del DEX (ej: "uniswap-arbitrum", "pancakeswap-bsc")
        private_key: Clave privada para firmar transacciones
    
    Returns:
        Instancia del adapter correspondiente
    
    Raises:
        ValueError: Si el DEX no está soportado
    """
    if dex_id not in DEX_CONFIGS:
        raise ValueError(f"DEX no soportado: {dex_id}. "
                        f"Disponibles: {list(DEX_CONFIGS.keys())}")
    
    config = DEX_CONFIGS[dex_id]
    
    if dex_id.startswith("uniswap"):
        return UniswapV3Adapter(config, private_key)
    elif dex_id.startswith("pancakeswap"):
        return PancakeSwapV3Adapter(config, private_key)
    elif dex_id.startswith("sushiswap"):
        return SushiSwapV3Adapter(config, private_key)
    else:
        raise ValueError(f"Tipo de DEX desconocido: {dex_id}")


def list_available_dexes() -> List[Dict]:
    """Lista todos los DEXs disponibles con sus chains"""
    result = []
    for dex_id, config in DEX_CONFIGS.items():
        result.append({
            "id": dex_id,
            "name": config.name,
            "chain": config.chain,
            "native_token": config.native_token,
            "default_fee_tier": config.default_fee_tier,
            "explorer": config.explorer_url,
        })
    return result
