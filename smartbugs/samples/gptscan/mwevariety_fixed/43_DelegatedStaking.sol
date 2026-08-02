// mwevariety_fixed: aus Web3Bugs-Originalquellen geflattet (siehe corpus_tools/build_fixed.py)
// SPDX-License-Identifier: MIT
pragma solidity 0.8.36;

// ---- C:\Users\Carlo\Desktop\Familie\Alex\Uni\BACHELORARBEIT\Github\BA\corpus_tools\vendor\43@0.8\@openzeppelin\contracts-upgradeable\token\ERC20\IERC20Upgradeable.sol ----
// license-stripped



/**
 * @dev Interface of the ERC20 standard as defined in the EIP.
 */
interface IERC20Upgradeable {
    /**
     * @dev Returns the amount of tokens in existence.
     */
    function totalSupply() external view returns (uint256);

    /**
     * @dev Returns the amount of tokens owned by `account`.
     */
    function balanceOf(address account) external view returns (uint256);

    /**
     * @dev Moves `amount` tokens from the caller's account to `recipient`.
     *
     * Returns a boolean value indicating whether the operation succeeded.
     *
     * Emits a {Transfer} event.
     */
    function transfer(address recipient, uint256 amount) external returns (bool);

    /**
     * @dev Returns the remaining number of tokens that `spender` will be
     * allowed to spend on behalf of `owner` through {transferFrom}. This is
     * zero by default.
     *
     * This value changes when {approve} or {transferFrom} are called.
     */
    function allowance(address owner, address spender) external view returns (uint256);

    /**
     * @dev Sets `amount` as the allowance of `spender` over the caller's tokens.
     *
     * Returns a boolean value indicating whether the operation succeeded.
     *
     * IMPORTANT: Beware that changing an allowance with this method brings the risk
     * that someone may use both the old and the new allowance by unfortunate
     * transaction ordering. One possible solution to mitigate this race
     * condition is to first reduce the spender's allowance to 0 and set the
     * desired value afterwards:
     * https://github.com/ethereum/EIPs/issues/20#issuecomment-263524729
     *
     * Emits an {Approval} event.
     */
    function approve(address spender, uint256 amount) external returns (bool);

    /**
     * @dev Moves `amount` tokens from `sender` to `recipient` using the
     * allowance mechanism. `amount` is then deducted from the caller's
     * allowance.
     *
     * Returns a boolean value indicating whether the operation succeeded.
     *
     * Emits a {Transfer} event.
     */
    function transferFrom(
        address sender,
        address recipient,
        uint256 amount
    ) external returns (bool);

    /**
     * @dev Emitted when `value` tokens are moved from one account (`from`) to
     * another (`to`).
     *
     * Note that `value` may be zero.
     */
    event Transfer(address indexed from, address indexed to, uint256 value);

    /**
     * @dev Emitted when the allowance of a `spender` for an `owner` is set by
     * a call to {approve}. `value` is the new allowance.
     */
    event Approval(address indexed owner, address indexed spender, uint256 value);
}

// ---- C:\Users\Carlo\Desktop\Familie\Alex\Uni\BACHELORARBEIT\Github\BA\corpus_tools\vendor\43@0.8\@openzeppelin\contracts-upgradeable\proxy\utils\Initializable.sol ----
// license-stripped



/**
 * @dev This is a base contract to aid in writing upgradeable contracts, or any kind of contract that will be deployed
 * behind a proxy. Since a proxied contract can't have a constructor, it's common to move constructor logic to an
 * external initializer function, usually called `initialize`. It then becomes necessary to protect this initializer
 * function so it can only be called once. The {initializer} modifier provided by this contract will have this effect.
 *
 * TIP: To avoid leaving the proxy in an uninitialized state, the initializer function should be called as early as
 * possible by providing the encoded function call as the `_data` argument to {ERC1967Proxy-constructor}.
 *
 * CAUTION: When used with inheritance, manual care must be taken to not invoke a parent initializer twice, or to ensure
 * that all initializers are idempotent. This is not verified automatically as constructors are by Solidity.
 */
abstract contract Initializable {
    /**
     * @dev Indicates that the contract has been initialized.
     */
    bool private _initialized;

    /**
     * @dev Indicates that the contract is in the process of being initialized.
     */
    bool private _initializing;

    /**
     * @dev Modifier to protect an initializer function from being invoked twice.
     */
    modifier initializer() {
        require(_initializing || !_initialized, "Initializable: contract is already initialized");

        bool isTopLevelCall = !_initializing;
        if (isTopLevelCall) {
            _initializing = true;
            _initialized = true;
        }

        _;

        if (isTopLevelCall) {
            _initializing = false;
        }
    }
}

// ---- C:\Users\Carlo\Desktop\Familie\Alex\Uni\BACHELORARBEIT\Github\BA\corpus_tools\vendor\43@0.8\@openzeppelin\contracts-upgradeable\utils\ContextUpgradeable.sol ----
// license-stripped




/**
 * @dev Provides information about the current execution context, including the
 * sender of the transaction and its data. While these are generally available
 * via msg.sender and msg.data, they should not be accessed in such a direct
 * manner, since when dealing with meta-transactions the account sending and
 * paying for execution may not be the actual sender (as far as an application
 * is concerned).
 *
 * This contract is only required for intermediate, library-like contracts.
 */
abstract contract ContextUpgradeable is Initializable {
    function __Context_init() internal initializer {
        __Context_init_unchained();
    }

    function __Context_init_unchained() internal initializer {
    }
    function _msgSender() internal view virtual returns (address) {
        return msg.sender;
    }

    function _msgData() internal view virtual returns (bytes calldata) {
        return msg.data;
    }
    uint256[50] private __gap;
}

// ---- C:\Users\Carlo\Desktop\Familie\Alex\Uni\BACHELORARBEIT\Github\BA\corpus_tools\vendor\43@0.8\@openzeppelin\contracts-upgradeable\access\OwnableUpgradeable.sol ----
// license-stripped






/**
 * @dev Contract module which provides a basic access control mechanism, where
 * there is an account (an owner) that can be granted exclusive access to
 * specific functions.
 *
 * By default, the owner account will be the one that deploys the contract. This
 * can later be changed with {transferOwnership}.
 *
 * This module is used through inheritance. It will make available the modifier
 * `onlyOwner`, which can be applied to your functions to restrict their use to
 * the owner.
 */
abstract contract OwnableUpgradeable is Initializable, ContextUpgradeable {
    address private _owner;

    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    /**
     * @dev Initializes the contract setting the deployer as the initial owner.
     */
    function __Ownable_init() internal initializer {
        __Context_init_unchained();
        __Ownable_init_unchained();
    }

    function __Ownable_init_unchained() internal initializer {
        _setOwner(_msgSender());
    }

    /**
     * @dev Returns the address of the current owner.
     */
    function owner() public view virtual returns (address) {
        return _owner;
    }

    /**
     * @dev Throws if called by any account other than the owner.
     */
    modifier onlyOwner() {
        require(owner() == _msgSender(), "Ownable: caller is not the owner");
        _;
    }

    /**
     * @dev Leaves the contract without owner. It will not be possible to call
     * `onlyOwner` functions anymore. Can only be called by the current owner.
     *
     * NOTE: Renouncing ownership will leave the contract without an owner,
     * thereby removing any functionality that is only available to the owner.
     */
    function renounceOwnership() public virtual onlyOwner {
        _setOwner(address(0));
    }

    /**
     * @dev Transfers ownership of the contract to a new account (`newOwner`).
     * Can only be called by the current owner.
     */
    function transferOwnership(address newOwner) public virtual onlyOwner {
        require(newOwner != address(0), "Ownable: new owner is the zero address");
        _setOwner(newOwner);
    }

    function _setOwner(address newOwner) private {
        address oldOwner = _owner;
        _owner = newOwner;
        emit OwnershipTransferred(oldOwner, newOwner);
    }
    uint256[49] private __gap;
}

// ---- C:\Users\Carlo\Desktop\Familie\Alex\Uni\BACHELORARBEIT\Github\BA\corpus_tools\vendor\43@0.8\@openzeppelin\contracts-upgradeable\utils\AddressUpgradeable.sol ----
// license-stripped



/**
 * @dev Collection of functions related to the address type
 */
library AddressUpgradeable {
    /**
     * @dev Returns true if `account` is a contract.
     *
     * [IMPORTANT]
     * ====
     * It is unsafe to assume that an address for which this function returns
     * false is an externally-owned account (EOA) and not a contract.
     *
     * Among others, `isContract` will return false for the following
     * types of addresses:
     *
     *  - an externally-owned account
     *  - a contract in construction
     *  - an address where a contract will be created
     *  - an address where a contract lived, but was destroyed
     * ====
     */
    function isContract(address account) internal view returns (bool) {
        // This method relies on extcodesize, which returns 0 for contracts in
        // construction, since the code is only stored at the end of the
        // constructor execution.

        uint256 size;
        assembly {
            size := extcodesize(account)
        }
        return size > 0;
    }

    /**
     * @dev Replacement for Solidity's `transfer`: sends `amount` wei to
     * `recipient`, forwarding all available gas and reverting on errors.
     *
     * https://eips.ethereum.org/EIPS/eip-1884[EIP1884] increases the gas cost
     * of certain opcodes, possibly making contracts go over the 2300 gas limit
     * imposed by `transfer`, making them unable to receive funds via
     * `transfer`. {sendValue} removes this limitation.
     *
     * https://diligence.consensys.net/posts/2019/09/stop-using-soliditys-transfer-now/[Learn more].
     *
     * IMPORTANT: because control is transferred to `recipient`, care must be
     * taken to not create reentrancy vulnerabilities. Consider using
     * {ReentrancyGuard} or the
     * https://solidity.readthedocs.io/en/v0.5.11/security-considerations.html#use-the-checks-effects-interactions-pattern[checks-effects-interactions pattern].
     */
    function sendValue(address payable recipient, uint256 amount) internal {
        require(address(this).balance >= amount, "Address: insufficient balance");

        (bool success, ) = recipient.call{value: amount}("");
        require(success, "Address: unable to send value, recipient may have reverted");
    }

    /**
     * @dev Performs a Solidity function call using a low level `call`. A
     * plain `call` is an unsafe replacement for a function call: use this
     * function instead.
     *
     * If `target` reverts with a revert reason, it is bubbled up by this
     * function (like regular Solidity function calls).
     *
     * Returns the raw returned data. To convert to the expected return value,
     * use https://solidity.readthedocs.io/en/latest/units-and-global-variables.html?highlight=abi.decode#abi-encoding-and-decoding-functions[`abi.decode`].
     *
     * Requirements:
     *
     * - `target` must be a contract.
     * - calling `target` with `data` must not revert.
     *
     * _Available since v3.1._
     */
    function functionCall(address target, bytes memory data) internal returns (bytes memory) {
        return functionCall(target, data, "Address: low-level call failed");
    }

    /**
     * @dev Same as {xref-Address-functionCall-address-bytes-}[`functionCall`], but with
     * `errorMessage` as a fallback revert reason when `target` reverts.
     *
     * _Available since v3.1._
     */
    function functionCall(
        address target,
        bytes memory data,
        string memory errorMessage
    ) internal returns (bytes memory) {
        return functionCallWithValue(target, data, 0, errorMessage);
    }

    /**
     * @dev Same as {xref-Address-functionCall-address-bytes-}[`functionCall`],
     * but also transferring `value` wei to `target`.
     *
     * Requirements:
     *
     * - the calling contract must have an ETH balance of at least `value`.
     * - the called Solidity function must be `payable`.
     *
     * _Available since v3.1._
     */
    function functionCallWithValue(
        address target,
        bytes memory data,
        uint256 value
    ) internal returns (bytes memory) {
        return functionCallWithValue(target, data, value, "Address: low-level call with value failed");
    }

    /**
     * @dev Same as {xref-Address-functionCallWithValue-address-bytes-uint256-}[`functionCallWithValue`], but
     * with `errorMessage` as a fallback revert reason when `target` reverts.
     *
     * _Available since v3.1._
     */
    function functionCallWithValue(
        address target,
        bytes memory data,
        uint256 value,
        string memory errorMessage
    ) internal returns (bytes memory) {
        require(address(this).balance >= value, "Address: insufficient balance for call");
        require(isContract(target), "Address: call to non-contract");

        (bool success, bytes memory returndata) = target.call{value: value}(data);
        return verifyCallResult(success, returndata, errorMessage);
    }

    /**
     * @dev Same as {xref-Address-functionCall-address-bytes-}[`functionCall`],
     * but performing a static call.
     *
     * _Available since v3.3._
     */
    function functionStaticCall(address target, bytes memory data) internal view returns (bytes memory) {
        return functionStaticCall(target, data, "Address: low-level static call failed");
    }

    /**
     * @dev Same as {xref-Address-functionCall-address-bytes-string-}[`functionCall`],
     * but performing a static call.
     *
     * _Available since v3.3._
     */
    function functionStaticCall(
        address target,
        bytes memory data,
        string memory errorMessage
    ) internal view returns (bytes memory) {
        require(isContract(target), "Address: static call to non-contract");

        (bool success, bytes memory returndata) = target.staticcall(data);
        return verifyCallResult(success, returndata, errorMessage);
    }

    /**
     * @dev Tool to verifies that a low level call was successful, and revert if it wasn't, either by bubbling the
     * revert reason using the provided one.
     *
     * _Available since v4.3._
     */
    function verifyCallResult(
        bool success,
        bytes memory returndata,
        string memory errorMessage
    ) internal pure returns (bytes memory) {
        if (success) {
            return returndata;
        } else {
            // Look for revert reason and bubble it up if present
            if (returndata.length > 0) {
                // The easiest way to bubble the revert reason is using memory via assembly

                assembly {
                    let returndata_size := mload(returndata)
                    revert(add(32, returndata), returndata_size)
                }
            } else {
                revert(errorMessage);
            }
        }
    }
}

// ---- C:\Users\Carlo\Desktop\Familie\Alex\Uni\BACHELORARBEIT\Github\BA\corpus_tools\vendor\43@0.8\@openzeppelin\contracts-upgradeable\token\ERC20\utils\SafeERC20Upgradeable.sol ----
// license-stripped






/**
 * @title SafeERC20
 * @dev Wrappers around ERC20 operations that throw on failure (when the token
 * contract returns false). Tokens that return no value (and instead revert or
 * throw on failure) are also supported, non-reverting calls are assumed to be
 * successful.
 * To use this library you can add a `using SafeERC20 for IERC20;` statement to your contract,
 * which allows you to call the safe operations as `token.safeTransfer(...)`, etc.
 */
library SafeERC20Upgradeable {
    using AddressUpgradeable for address;

    function safeTransfer(
        IERC20Upgradeable token,
        address to,
        uint256 value
    ) internal {
        _callOptionalReturn(token, abi.encodeWithSelector(token.transfer.selector, to, value));
    }

    function safeTransferFrom(
        IERC20Upgradeable token,
        address from,
        address to,
        uint256 value
    ) internal {
        _callOptionalReturn(token, abi.encodeWithSelector(token.transferFrom.selector, from, to, value));
    }

    /**
     * @dev Deprecated. This function has issues similar to the ones found in
     * {IERC20-approve}, and its usage is discouraged.
     *
     * Whenever possible, use {safeIncreaseAllowance} and
     * {safeDecreaseAllowance} instead.
     */
    function safeApprove(
        IERC20Upgradeable token,
        address spender,
        uint256 value
    ) internal {
        // safeApprove should only be called when setting an initial allowance,
        // or when resetting it to zero. To increase and decrease it, use
        // 'safeIncreaseAllowance' and 'safeDecreaseAllowance'
        require(
            (value == 0) || (token.allowance(address(this), spender) == 0),
            "SafeERC20: approve from non-zero to non-zero allowance"
        );
        _callOptionalReturn(token, abi.encodeWithSelector(token.approve.selector, spender, value));
    }

    function safeIncreaseAllowance(
        IERC20Upgradeable token,
        address spender,
        uint256 value
    ) internal {
        uint256 newAllowance = token.allowance(address(this), spender) + value;
        _callOptionalReturn(token, abi.encodeWithSelector(token.approve.selector, spender, newAllowance));
    }

    function safeDecreaseAllowance(
        IERC20Upgradeable token,
        address spender,
        uint256 value
    ) internal {
        unchecked {
            uint256 oldAllowance = token.allowance(address(this), spender);
            require(oldAllowance >= value, "SafeERC20: decreased allowance below zero");
            uint256 newAllowance = oldAllowance - value;
            _callOptionalReturn(token, abi.encodeWithSelector(token.approve.selector, spender, newAllowance));
        }
    }

    /**
     * @dev Imitates a Solidity high-level call (i.e. a regular function call to a contract), relaxing the requirement
     * on the return value: the return value is optional (but if data is returned, it must not be false).
     * @param token The token targeted by the call.
     * @param data The call data (encoded using abi.encode or one of its variants).
     */
    function _callOptionalReturn(IERC20Upgradeable token, bytes memory data) private {
        // We need to perform a low level call here, to bypass Solidity's return data size checking mechanism, since
        // we're implementing it ourselves. We use {Address.functionCall} to perform this call, which verifies that
        // the target address contains contract code and also asserts for success in the low-level call.

        bytes memory returndata = address(token).functionCall(data, "SafeERC20: low-level call failed");
        if (returndata.length > 0) {
            // Return data is optional
            require(abi.decode(returndata, (bool)), "SafeERC20: ERC20 operation did not succeed");
        }
    }
}

// ---- 43\contracts\DelegatedStaking.sol ----
//license-stripped






contract DelegatedStaking is OwnableUpgradeable{
    using SafeERC20Upgradeable for IERC20Upgradeable;
    uint256 constant divider = 10**18; // 18 decimals used for scaling the rates
    uint128 validatorCoolDown; // how many epochs until validator unstaking is unlocked
    uint128 delegatorCoolDown; // how many epochs until delegator unstaking is unlocked
    uint128 maxCapMultiplier;
    uint128 validatorMinStakedRequired; // minimum # of tokens validator is required to have staked
    uint128 allocatedTokensPerEpoch; // # of tokens per epoch to be distributed
    uint128 rewardsLocked; // # of tokens the owner sent to the contract
    uint128 endEpoch; // the epoch when the contract will be out of allocated reward tokens
    uint128 totalGlobalShares; // global shares
    uint128 lastUpdateEpoch; // block # when the global exchange rate was updated last
    uint128 globalExchangeRate;
    uint128 validatorsN; // number of validators, used to get validator ids
    mapping(uint128 => Validator) validators; // id -> validator instance
    IERC20Upgradeable constant CQT = IERC20Upgradeable(0xD417144312DbF50465b1C641d016962017Ef6240);

    struct Staking {
        uint128 staked; // initial CQT amount staked
        uint128 shares; // # of validator shares that delegate owns
    }
    struct Unstaking {
        uint128 coolDownEnd; // epoch when unstaking can be redeemed
        uint128 amount;
    }
    struct Validator {
        address _address;
        address operator;
        uint128 commissionRate; // validator commission rate
        uint128 disabledEpoch; // epoch when validator got disabled, if set to 0, validator is enabled
        uint128 globalShares; // total number of global shares under a validator
        uint128 lastUpdateGlobalRate; // global exchange rate when the validator was updated the last time
        uint128 totalShares; // total number of validator shares
        uint128 delegated; // total number of tokens originally staked/delegated to the validator, this does not include interest
        uint128 exchangeRate; // validator exchange rate
        uint128 commissionAvailableToRedeem; // # of CQTs paid to the validator
        mapping(address => Staking) stakings;
        mapping(address => Unstaking[]) unstakings;
    }
    event RewardTokensDeposited(uint128 amount);
    event ValidatorAdded(uint128 indexed id, address indexed validator, address indexed operator);
    event ValidatorDisabled(uint128 indexed id);
    event Staked(uint128 indexed validatorId, address delegator, uint128 amount);
    event Unstaked(uint128 indexed validatorId, address indexed delegator, uint128 amount);
    event RecoveredUnstake(uint128 indexed validatorId, address indexed delegator, uint128 amount, uint128 unstakingId);
    event UnstakeRedeemed(uint128 indexed validatorId, address indexed delegator, uint128 amount);
    event RewardRedeemed(uint128 indexed validatorId, address indexed beneficiary, uint128 amount);
    event CommissionRewardRedeemed(uint128 indexed validatorId, address indexed beneficiary, uint128 amount);
    event AllocatedTokensTaken(uint128 amount);
    event MaxCapMultiplierChanged(uint128 amount);
    event TransferredUnstake(uint128 indexed oldValidatorId, uint128 indexed newValidatorId, address indexed delegator, uint128 amount, uint128 unstakingId);
    event EmissionRateChanged(uint128 newRate);
    event ValidatorCommissionRateChanged(uint128 indexed validatorId, uint128 newRate);
    event ValidatorMinStakedRequiredChanged(uint128 amount);
    event Initialized(uint128 minStakedRequired, uint128 validatorCoolDown, uint128 delegatorCoolDown, uint128 maxCapMultiplier, uint128 allocatedTokensPerEpoch, uint128 globalExchangeRate);

    // this is used to have the contract upgradeable
    function initialize(uint128 minStakedRequired) public initializer {
        __Ownable_init();
        validatorMinStakedRequired = minStakedRequired;
        validatorCoolDown = 180*6646; // ~ 6 months
        delegatorCoolDown = 28*6646; // ~ 28 days
        maxCapMultiplier = 10;
        allocatedTokensPerEpoch = 1*10**18; // should never be 0
        globalExchangeRate = 10**18; // 1 to 1
        emit Initialized(minStakedRequired, validatorCoolDown, delegatorCoolDown, maxCapMultiplier, allocatedTokensPerEpoch, globalExchangeRate);
    }

    // used to transfer CQT from delegators, validators and the owner to the contract
    function _transferToContract(address from, uint128 amount) internal {
        CQT.safeTransferFrom(from, address(this), amount);
    }

    // used to transfer CQT from contract, for rewards redemption or transferring out unstaked
    function _transferFromContract(address to, uint128 amount) internal {
        CQT.safeTransfer(to, amount);
    }

    // transfer CQT from the owner to the contract for rewards allocation, must change end epoch
    function depositRewardTokens(uint128 amount) public onlyOwner {
        require(amount >= allocatedTokensPerEpoch, "Does not cover least 1 epoch");
        require(amount % allocatedTokensPerEpoch == 0, "Not multiple");
        if (endEpoch != 0) {
            unchecked { endEpoch += amount / allocatedTokensPerEpoch; }
        }
        else{
            unchecked { rewardsLocked += amount; }
        }
        _transferToContract(msg.sender, amount);
        emit RewardTokensDeposited(amount);
    }

    // transfer reward CQT from the contract to the owner, must change end epoch and not allow transfer from the past
    function takeOutRewardTokens(uint128 amount) public onlyOwner {
        require(amount > 0, "Amount is 0");
        require(amount % allocatedTokensPerEpoch == 0, "Not multiple");
        if (endEpoch != 0){
            uint128 currentEpoch = uint128(block.number);
            uint128 epochs = amount / allocatedTokensPerEpoch;
            require(endEpoch - epochs > currentEpoch, "Cannot takeout rewards from past");
            unchecked { endEpoch = endEpoch - epochs; }
        }
        else{
            require(rewardsLocked >= amount, "Amount is greater than available");
            unchecked { rewardsLocked -= amount; }
        }
        _transferFromContract(msg.sender, amount);
        emit AllocatedTokensTaken(amount);
    }

    // update global exchange rate
    function _updateGlobalExchangeRate() internal {
        uint128 currentBlock = uint128(block.number);
        // if the program ended, set update epoch to the end epoch
        uint128 currentEpoch = currentBlock < endEpoch? currentBlock : endEpoch;
        if (currentEpoch != lastUpdateEpoch){
            // when no one has staked anything, do not update the rate
            if(totalGlobalShares > 0)
            {
                unchecked { globalExchangeRate += uint128(uint256(allocatedTokensPerEpoch) * divider * uint256(currentEpoch - lastUpdateEpoch)/uint256(totalGlobalShares)) ; }
            }
            lastUpdateEpoch = currentEpoch;
        }
    }

    // update validator exchange rate
    function _updateValidator(Validator storage v) internal {
        // if validator is disabled, we do not update it since it was updated during disabling transaction
        if(v.disabledEpoch == 0){
            if (v.totalShares == 0){
                // when validator stakes the first time, the exchange rate must be equal to the current global exchange rate
                v.exchangeRate = globalExchangeRate;
            }
            else {
                // the growth of global exchange rate since the validator was updated the last time
                uint128 rateDifference;
                unchecked { rateDifference = globalExchangeRate - v.lastUpdateGlobalRate; }
                // tokens given to the validator and its delegators since last update
                uint128 tokensGivenToValidator = _sharesToTokens(v.globalShares, rateDifference);
                // commission paid out of the tokens
                uint128 commissionPaid = uint128(uint256(tokensGivenToValidator) * uint256(v.commissionRate) /  divider);
                // increase validator exchange rate by distributing the leftover tokens through the validator shares
                v.exchangeRate += uint128(uint256(tokensGivenToValidator - commissionPaid) * divider / v.totalShares);
                // give commission tokens to the validator
                unchecked { v.commissionAvailableToRedeem += commissionPaid; }
            }
            // set the last update global rate to the current one
            v.lastUpdateGlobalRate = globalExchangeRate;
        }
    }
    // used to convert global shares or validator shares to CQT
    function _sharesToTokens(uint128 sharesN, uint128 rate) internal view returns(uint128){
        return uint128(uint256(sharesN) * uint256(rate) / divider);
    }
    // used to convert CQT to global shares or validator shares
    function _tokensToShares(uint128 amount, uint128 rate) internal view returns(uint128){
        return uint128(uint256(amount) * divider / uint256(rate));
    }

    function stake(uint128 validatorId, uint128 amount) public {
        _stake(validatorId, amount, true);
    }
    // need to update global exchange rate, validator data and then delegator instance
    // withTransfer set to false when delegators recover unstake, because the tokens are already in the contract
    function _stake(uint128 validatorId, uint128 amount, bool withTransfer) internal {
        require(amount >= divider, "Amount must be at least 1 token");
        require(validatorId < validatorsN, "Invalid validator");
        Validator storage v = validators[validatorId];
        require(v.disabledEpoch == 0, "Validator is disabled");
        // if this is the first stake, then set the end epoch
        if (endEpoch == 0){
            unchecked { endEpoch = uint128(block.number) + rewardsLocked / allocatedTokensPerEpoch; }
            rewardsLocked = 0; // no longer used and saves a bit of gas
        }
        require(endEpoch > block.number, "Program ended");
        _updateGlobalExchangeRate();
        _updateValidator(v);
        // if staker is validator who self delegates
        if (msg.sender == v._address){
            require(amount + v.stakings[msg.sender].staked >= validatorMinStakedRequired, "Amount < min staked required");
        }
        else {
            // otherwise need to check for max cap
            uint128 validatorStaked = v.stakings[v._address].staked;
            uint128 validatorMaxCap = validatorStaked * maxCapMultiplier;
            uint128 newDelegated = v.delegated - validatorStaked + amount;
            require(newDelegated <= validatorMaxCap, "Validator max capacity exceeded");
        }
        // it is set to true when there is a stake
        // it is set to false when we recover delegation from unstaking
        if (withTransfer)
            _transferToContract(msg.sender, amount);
        Staking storage s = v.stakings[msg.sender];

        // update global shares #
        uint128 globalSharesToAdd = _tokensToShares(amount, globalExchangeRate);
        unchecked { totalGlobalShares += globalSharesToAdd; }
        unchecked { v.globalShares += globalSharesToAdd; }

        // update validator shares #
        uint128 newDelegatorSharesN = _tokensToShares(amount, v.exchangeRate);
        unchecked { v.totalShares += newDelegatorSharesN; }
        unchecked { s.shares += newDelegatorSharesN; }
        unchecked { v.delegated += amount; }
        unchecked { s.staked += amount; }
        emit Staked(validatorId, msg.sender, amount);
    }

    // need to update global exchange rate, validator data and then delegator instance
    function unstake(uint128 validatorId, uint128 amount) public {
        require(validatorId < validatorsN, "Invalid validator");
        Validator storage v = validators[validatorId];
        Staking storage s = v.stakings[msg.sender];
        require(s.staked >= amount, "Staked < amount provided");
        bool isValidator = msg.sender == v._address;
        _updateGlobalExchangeRate();
        _updateValidator(v);
        // only update if the validator is enabled, otherwise the global shares were already excluded during disableValidator call and the rest does not matter anymore
        uint128 validatorSharesRemove = _tokensToShares(amount, v.exchangeRate);
        require(validatorSharesRemove > 0, "Unstake amount is too small");
        if (v.disabledEpoch == 0){
            // if validator is enabled and the program has not ended -> check for unstaking beyond max cap or min stake required
            if (isValidator && endEpoch > block.number){
                uint128 newValidatorStaked = s.staked - amount;
                uint128 newValidatorMaxCap = newValidatorStaked * maxCapMultiplier;
                uint128 delegated = v.delegated - s.staked;
                require(delegated <= newValidatorMaxCap, "Cannot unstake beyond max cap");
                require(newValidatorStaked >= validatorMinStakedRequired, "Unstake > min staked required");
            }

            // update global shares #
            uint128 globalSharesRemove = _tokensToShares(amount, globalExchangeRate);
            require(globalSharesRemove > 0, "Unstake amount is too small");
            unchecked { totalGlobalShares -= globalSharesRemove;}
            unchecked { v.globalShares -= globalSharesRemove; }

            // update validator shares #
            unchecked { v.totalShares -= validatorSharesRemove; }
            unchecked { v.delegated -= amount; }
        }
        unchecked { s.shares -= validatorSharesRemove; }
        unchecked { s.staked -= amount; }

        // create unstaking instance
        uint128 coolDownEnd = v.disabledEpoch != 0 ? v.disabledEpoch : uint128(block.number);
        unchecked { coolDownEnd += (isValidator ? validatorCoolDown : delegatorCoolDown); }
        v.unstakings[msg.sender].push(Unstaking( coolDownEnd, amount));
        emit Unstaked(validatorId, msg.sender, amount);
    }

    // restake unstaked tokens
    function recoverUnstaking(uint128 amount, uint128 validatorId, uint128 unstakingId) public{
        Unstaking storage us = validators[validatorId].unstakings[msg.sender][unstakingId];
        require(us.amount >= amount, "Unstaking has less tokens");
        _stake(validatorId, amount, false);
        us.amount -= amount;
        // set cool down end to 0 to release gas if new unstaking amount is 0
        if(us.amount == 0)
            us.coolDownEnd = 0;
        emit RecoveredUnstake(validatorId, msg.sender, amount, unstakingId);
    }

    // if amount is 0 then redeem all
    function _redeemRewards( uint128 validatorId, address beneficiary, uint128 amount) internal {
        require(beneficiary!=address(0x0), "Invalid beneficiary");
        _updateGlobalExchangeRate();
        Validator storage v = validators[validatorId];
        _updateValidator(v);
        Staking storage s = v.stakings[msg.sender];

        uint128 rewards = _sharesToTokens(s.shares, v.exchangeRate) - s.staked;
        if(msg.sender == v._address){
            if(amount == 0){
                unchecked { amount = rewards + v.commissionAvailableToRedeem; }
            }
            require(rewards + v.commissionAvailableToRedeem >= amount, "Redeem amount > available");
            // first redeem rewards from commission
            uint128 commissionLeftOver = amount < v.commissionAvailableToRedeem ? v.commissionAvailableToRedeem - amount : 0;
            // if there is more, redeem  it from regular rewards
            if (commissionLeftOver == 0){
                uint128 validatorSharesRemove = _tokensToShares(amount - v.commissionAvailableToRedeem, v.exchangeRate);
                unchecked { s.shares -= validatorSharesRemove; }
                unchecked { v.totalShares -= validatorSharesRemove; }
            }
            emit CommissionRewardRedeemed(validatorId, beneficiary, v.commissionAvailableToRedeem - commissionLeftOver);
            v.commissionAvailableToRedeem = commissionLeftOver;
        }
        else {
            if(amount == 0){
                amount = rewards;
            }
            require(rewards >= amount, "Redeem amount > available");
            uint128 validatorSharesRemove = _tokensToShares(amount, v.exchangeRate);
            unchecked { s.shares -= validatorSharesRemove; }
            unchecked { v.totalShares -= validatorSharesRemove; }
        }
        _transferFromContract(beneficiary, amount);

        // update global shares #
        // this includes commission and rewards earned
        // only update if the validator is enabled, otherwise the shares were already excluded during disableValidator call
        if (v.disabledEpoch == 0){
            uint128 globalSharesRemove = _tokensToShares(amount, globalExchangeRate);
            unchecked { totalGlobalShares -= globalSharesRemove; }
            unchecked { v.globalShares -= globalSharesRemove; }
        }
        emit RewardRedeemed(validatorId, beneficiary, amount);
    }

    // redeem all available rewards
    function redeemAllRewards( uint128 validatorId, address beneficiary) external {
        _redeemRewards(validatorId, beneficiary, 0);
    }

    // if validator calls redeem rewards, first tokens paid from comissions will be redeemed and then regular rewards
    function redeemRewards( uint128 validatorId, address beneficiary, uint128 amount) external {
        require(amount > 0, "Amount is 0");
        _redeemRewards(validatorId, beneficiary, amount);
    }

    // add new validator instance
    function addValidator(address validator, address operator, uint128 commissionRate) public onlyOwner {
        require(commissionRate < divider, "Rate must be less than 100%");
        uint128 N = validatorsN;
        validators[N]._address = validator;
        validators[N].operator = operator;
        validators[N].commissionRate = commissionRate;
        emit ValidatorAdded(N, validator, operator);
        unchecked { validatorsN += 1; }
    }

    // can only be called by the owner or the validator, disabling will allow validator to fully unstake
    // validator instance can only be disabled once and can never be reenabled
    function disableValidator(uint128 validatorId) public {
        Validator storage v = validators[validatorId];
        require(v.disabledEpoch == 0, "Validator is already disabled");
        require(v._address == msg.sender || msg.sender == owner(), "Caller is not owner or validator");
        _updateGlobalExchangeRate();
        _updateValidator(v);
        v.disabledEpoch = uint128(block.number) < endEpoch? uint128(block.number) : endEpoch;
        unchecked { totalGlobalShares -= v.globalShares; }
        emit ValidatorDisabled(validatorId);
    }

    // change emission rate, should reset end epoch
    function setAllocatedTokensPerEpoch(uint128 amount) public onlyOwner {
        require(amount > 0, "Amount is 0");
        uint128 toTransfer;
        if (endEpoch != 0){
            _updateGlobalExchangeRate();
            // get number of epochs from now to the end epoch
            uint128 epochs = endEpoch > uint128(block.number) ? endEpoch - uint128(block.number) : 0;
            // calculate how much rewards would be distributed with the old emission rate
            uint128 futureRewards = allocatedTokensPerEpoch * epochs;
            // calculate how many epochs will be covered
            uint128 addEpochs = futureRewards / amount;
            toTransfer = futureRewards % amount;
            require(addEpochs != 0, "This amount will end the program");
            unchecked { endEpoch = uint128(block.number) + addEpochs; }
        }
        else {
          toTransfer = rewardsLocked % amount;
        }
        allocatedTokensPerEpoch = amount;
        emit EmissionRateChanged(amount);
        if(toTransfer > 0)
            _transferFromContract(msg.sender, toTransfer);

    }

    // we assume that we will never set it to less than what is staked already
    function setMaxCapMultiplier(uint128 amount) public onlyOwner {
        require(amount > 0, "Must be greater than 0");
        maxCapMultiplier = amount;
        emit MaxCapMultiplierChanged(amount);
    }

    // only owner can change commission rate
    function setValidatorCommissionRate(uint128 amount, uint128 validatorId) public onlyOwner {
        require(amount < divider, "Rate must be less than 100%");
        _updateGlobalExchangeRate();
        _updateValidator(validators[validatorId]);
        validators[validatorId].commissionRate = amount;
        emit ValidatorCommissionRateChanged(validatorId, amount);
    }

    // we are assuming there will never be a case when the owner sets the value to something extremely big and if that happens accidentally, we will just recall the function
    function setValidatorMinStakedRequired(uint128 amount) public onlyOwner {
        validatorMinStakedRequired = amount;
        emit ValidatorMinStakedRequiredChanged(amount);
    }

    // if a validator gets disabled, delegators can redelegate their tokens to another validator
    // first they need to unstake
    function redelegateUnstaked(uint128 amount, uint128 oldValidatorId, uint128 newValidatorId, uint128 unstakingId) public {
        require(validators[oldValidatorId].disabledEpoch != 0, "Validator is not disabled");
        require(validators[oldValidatorId]._address != msg.sender, "Validator cannot redelegate");
        Unstaking storage us = validators[oldValidatorId].unstakings[msg.sender][unstakingId];
        require(us.amount >= amount, "Unstaking has less tokens");
        _stake(newValidatorId, amount, false);
        unchecked { us.amount -= amount; }
        // set cool down end to 0 to release gas if new unstaking amount is 0
        if(us.amount == 0)
            us.coolDownEnd = 0;
        emit TransferredUnstake(oldValidatorId, newValidatorId, msg.sender, amount, unstakingId);
    }

    // transfer out unlocked unstaked tokens back to the delegator
    function transferUnstakedOut(uint128 amount, uint128 validatorId, uint128 unstakingId) public {
        Unstaking storage us = validators[validatorId].unstakings[msg.sender][unstakingId];
        require( uint128(block.number) > us.coolDownEnd, "Cooldown period has not ended" );
        require(us.amount >= amount, "Amount is too high");
        _transferFromContract(msg.sender, amount);
        unchecked { us.amount -= amount; }
        // set cool down end to 0 to release gas if new unstaking amount is 0
        if (us.amount == 0)
            us.coolDownEnd = 0;
        emit UnstakeRedeemed(validatorId, msg.sender, amount);
    }

    // returns details of each validator
    // array index is id
    function getValidatorsDetails() public view returns (uint128[] memory commissionRates, uint128[] memory delegated) {
        commissionRates = new uint128[](validatorsN);
        delegated = new uint128[](validatorsN);
        for (uint128 i = 0; i < validatorsN; ++i){
            Validator storage v = validators[i];
            commissionRates[i] = v.commissionRate;
            delegated[i] = v.delegated - v.stakings[v._address].staked;
        }
        return (commissionRates, delegated);
    }

    // this follows the same logic as _updateGlobalExchangeRate and _updateValidator
    // array index is id of validator
    function getDelegatorDetails(address delegator) public view returns( uint128[] memory delegated,  uint128[] memory rewardsAvailable, uint128[] memory commissionRewards) {
       delegated = new uint128[](validatorsN);
       rewardsAvailable = new uint128[](validatorsN);
       commissionRewards = new uint128[](validatorsN);
       uint256 currentEpoch = block.number < endEpoch? block.number: endEpoch;
       uint128 newGlobalExchangeRate = uint128((uint256(allocatedTokensPerEpoch) * divider/totalGlobalShares)*(currentEpoch - lastUpdateEpoch)) + globalExchangeRate;
       Validator storage v;
       Staking storage s;
        for (uint128 i = 0; i < validatorsN; ++i){
            v = validators[i];
            s = v.stakings[delegator];
            delegated[i] = s.staked;
            if (v.disabledEpoch == 0){
                uint128 newTokensGiven = _sharesToTokens(v.globalShares, newGlobalExchangeRate - v.lastUpdateGlobalRate);
                uint128 commissionPaid = uint128(uint256(newTokensGiven) * uint256(v.commissionRate) /  divider);
                uint128 rateIncrease = uint128(uint256(newTokensGiven - commissionPaid) * divider / v.totalShares);
                rewardsAvailable[i] = _sharesToTokens(s.shares, v.exchangeRate + rateIncrease) - s.staked;
                if(delegator == v._address)
                    commissionRewards[i] = v.commissionAvailableToRedeem + commissionPaid;
            }
            else {
                rewardsAvailable[i] = _sharesToTokens(s.shares, v.exchangeRate) - s.staked;
                if(delegator == v._address)
                    commissionRewards[i] = v.commissionAvailableToRedeem;
            }
        }
        return (delegated, rewardsAvailable, commissionRewards);
    }

    function getMetadata() public view returns(uint128,  uint128, uint128, uint128, uint128 ){
        uint128 totalStaked = uint128(uint256(totalGlobalShares) * uint256(globalExchangeRate) / divider);
        return (allocatedTokensPerEpoch, endEpoch, maxCapMultiplier, totalStaked, validatorsN);
    }
}
